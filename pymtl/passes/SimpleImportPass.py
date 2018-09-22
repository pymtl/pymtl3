#-------------------------------------------------------------------------
# SimpleImportPass.py
#-------------------------------------------------------------------------
# SimpleImportPass class imports a Verilog/SystemVerilog source file
# back to a PyMTL RTLComponent. It is meant to be used with
# TranslationPass() as a PyMTL translation pass testing infrastructure. 
# This pass does the following steps:
# 1. Use verilator to compile the given Verilog source into C++.
# 2. Create a C++ wrapper that can call the Verilated model.
# 3. Compile the C++ wrapper and the Verilated model into a shared lib.
# 4. Create a Python wrapper that can call the compiled shared lib
#     through CFFI. 

import os
import shutil

from pymtl          import *
from BasePass       import BasePass
from subprocess			import check_output, STDOUT, CalledProcessError
from errors         import VerilatorCompileError
from SimRTLPass     import SimRTLPass

# Better indention

tab2 = '\n  '
tab4 = '\n    '
tab6 = '\n      '
tab8 = '\n        '

class SimpleImportPass( BasePass ):

  def __call__( s, model, verilog_file, top_module ):
    """ Import a Verilog/SystemVerilog file. top_module specifies
        the name of the top module. model is the PyMTL source of
        verilog_file. """

    ports = model.get_input_value_ports() | model.get_output_value_ports()
    
    # Generate Verilog and verilator names for all ports

    for port in ports:
      port.verilog_name   = s.generate_verilog_name( port._my_name )
      port.verilator_name = s.generate_verilator_name( port.verilog_name )
		
    s.create_verilator_model( verilog_file, top_module )

    c_wrapper = s.create_verilator_c_wrapper( model, top_module ) 

    lib_file = s.create_shared_lib( model, c_wrapper, top_module )

    s.create_verilator_py_wrapper( model, top_module, lib_file )

  def create_verilator_model( s, verilog_file, top_module ):
    """ Create a verilator file correspoding to the verilog_file model """

    # Prepare the verilator commandline

    verilator_cmd = '''verilator -cc {verilog_file} -top-module '''\
                    '''{top_module} --Mdir {obj_dir} -O3 {flags}'''

    obj_dir = 'obj_dir_' + top_module
    flags		= ' '.join( ['--unroll-count 1000000',
												 '--unroll-stmts 1000000',
												 '--assert',
												 '-Wno-UNOPTFLAT', 
											] )

    verilator_cmd = verilator_cmd.format( **vars() )

    # Remove obj_dir if already exists
    # It is the place where the verilator output is stored

    if os.path.exists( obj_dir ):
      shutil.rmtree( obj_dir )

    # Try to call verilator

    s.try_cmd( 'Calling verilator', verilator_cmd, VerilatorCompileError,
                shell = True )

  def create_verilator_c_wrapper( s, model, top_module ):
    """ create wrapper for verilated model so that later we can
        access it through cffi """

    # the template should be in the same directory as this file

    template_file = os.path.dirname( os.path.abspath( __file__ ) ) + \
                    os.path.sep + 'verilator_wrapper_template.c'

    verilator_c_wrapper_file = top_module + '_v.cpp'

    ports = model.get_input_value_ports() | model.get_output_value_ports()

    # Generate input and output ports for the verilated model

    port_externs = ''.join([ s.port_to_decl( x )+tab4 for x in ports ])

    # Generate initialization stmts for in/out ports

    port_inits   = ''.join([ s.port_to_init( x )+tab2 for x in ports ])

    with open( template_file, 'r' ) as template, \
         open( verilator_c_wrapper_file, 'w' ) as output:

          c_wrapper = template.read()
          c_wrapper = c_wrapper.format( top_module    = top_module,
                                        port_externs  = port_externs, 
                                        port_inits    = port_inits,
                                      )
          output.write( c_wrapper )

    return verilator_c_wrapper_file

  def create_shared_lib( s, model, c_wrapper, top_module ):
    ''' compile the Cpp wrapper and verilated model into a shared lib '''

    lib_file = 'lib{}_v.so'.format( top_module )

    # Assume $PYMTL_VERILATOR_INCLUDE_DIR is defined

    verilator_include_dir = os.environ.get( 'PYMTL_VERILATOR_INCLUDE_DIR' )

    include_dirs = [
          verilator_include_dir, 
          verilator_include_dir + '/vltstd',
        ]

    obj_dir_prefix = 'obj_dir_{}/V{}'.format( top_module, top_module )

    cpp_sources_list = []

    # Read through the makefile of the verilated model to find 
    # cpp files we need

    with open( obj_dir_prefix + "_classes.mk" ) as makefile:
      found = False
      for line in makefile:
        if line.startswith("VM_CLASSES_FAST += "):
          found = True
        elif found:
          if line.strip() == '':
            found = False
          else:
            filename = line.strip()[:-2]
            cpp_file = 'obj_dir_{}/{}.cpp'.format( top_module, filename )
            cpp_sources_list.append( cpp_file )

    # Complete the cpp sources file list

    cpp_sources_list += [
          obj_dir_prefix + '__Syms.cpp', 
          verilator_include_dir + '/verilated.cpp', 
          verilator_include_dir + '/verilated_dpi.cpp', 
          c_wrapper,
        ]

    # Call compiler with generated flags & dirs

    s.compile(
        flags           = '-O0 -fPIC -shared', 
        include_dirs    = include_dirs, 
        output_file     = lib_file, 
        input_files     = cpp_sources_list,
        )
    
    return lib_file

  def create_verilator_py_wrapper( s, model, top_module, lib_file ):
    ''' create a python wrapper that can manipulate the verilated model
    through the interfaces exposed by Cpp wrapper '''

    template_file = os.path.dirname( os.path.abspath( __file__ ) ) + \
                    os.path.sep + 'verilator_wrapper_template.py'

    verilator_py_wrapper_file = top_module + '_v.py'

    # Port definitions for verilated model

    port_externs  = []

    # Port definition in PyMTL style

    port_defs     = []

    # Set verilated input ports to PyMTL input ports

    set_inputs    = []

    # Combinational update block

    set_comb      = []

    # Sequential update block

    set_next      = []

    # Line trace 

    line_trace = s.generate_py_line_trace( model )

    # Internal line trace 

    in_line_trace = s.generate_py_internal_line_trace( model )

    # Create verilated model port definitions

    port_externs = ''.join( [ s.port_to_decl( x ) + tab8 for x in \
          model.get_input_value_ports() | model.get_output_value_ports() 
        ] )


    # Create PyMTL port definitions, input setting, comb stmts

    for port in model.get_input_value_ports():
      port_defs.append( '{name} = InVPort( Bits{nbits} )'.format(
          name = port._full_name, 
          nbits = port.Type.nbits,
        ) )
      if port._my_name == 'clk':
        continue
      set_inputs.extend( s.set_input_stmt( port ) )

    for port in model.get_output_value_ports():
      port_defs.append( '{name} = OutVPort( Bits{nbits} )'.format(
          name = port._full_name, 
          nbits = port.Type.nbits,
        ) )
      comb, next_ = s.set_output_stmt( port )
      set_comb.extend( comb )
      set_next.extend( next_ )

    # Read from template and fill in contents 

    with open( template_file, 'r' ) as template, \
         open( verilator_py_wrapper_file, 'w' ) as output:

      py_wrapper = template.read()
      py_wrapper = py_wrapper.format(
             top_module     = top_module,
             lib_file       = lib_file,
             port_externs   = port_externs,
             port_defs      = ''.join( [ x+tab4 for x in port_defs ] ),
             set_inputs     = ''.join( [ x+tab6 for x in set_inputs ] ),
             set_comb       = ''.join( [ x+tab6 for x in set_comb ] ),
             set_next       = ''.join( [ x+tab6 for x in set_next ] ),
             line_trace     = line_trace,
             in_line_trace  = in_line_trace,
          )
      output.write( py_wrapper )

    return verilator_py_wrapper_file

  #----------------------------------------------------------------------
  # Helper functions for SimpleImportPass
  #----------------------------------------------------------------------

  def try_cmd( s, name, cmd, exception = Exception, shell = False ):
    """ try to do name action with cmd command
        if the command fails, exception is raised
    """

    try:
      if shell:
        # for verilator compiling command
        ret = check_output( cmd, stderr=STDOUT, shell = True )
      else:
        # for compiling
        ret = check_output( cmd.split(), stderr=STDOUT, shell = shell )
    except CalledProcessError as e:
      error_msg = """
                    {name} error! 

                    Cmd:
                    {cmd}

                    Error:
                    {error}
                  """
      raise exception( error_msg.format( 
        name    = name, 
        cmd     = ' '.join( e.cmd ), 
        error   = e.output
      ) )

  def port_to_decl( s, port ):
    """ generate port declarations for port """
    ret = '{data_type} * {verilator_name};'

    verilator_name = port.verilator_name
    bitwidth       = port.Type.nbits

    if    bitwidth <= 8:   
      data_type = 'unsigned char'
    elif  bitwidth <= 16:  
      data_type = 'unsigned short'
    elif  bitwidth <= 32: 
      data_type = 'unsigned int'
    elif bitwidth <= 64:
      data_type = 'unsigned long'
    else:
      data_type = 'unsigned int'

    return ret.format( **locals() )

  def port_to_init( s, port ):
    """ generate port initializations for port """
    ret = 'm->{verilator_name} = {dereference}model->{verilator_name};'

    verilator_name = port.verilator_name
    bitwidth       = port.Type.nbits
    dereference    = '&' if bitwidth <= 64 else ''

    return ret.format( **locals() )

  def generate_verilog_name( s, name ):
    ''' generate a verilog-compliant name based on name '''
    return name.replace('.', '_')

  def generate_verilator_name( s, name ):
    ''' generate a verilator-compliant name based on name '''
    return name.replace( '__', '___05F' ).replace( '$', '__024' )

  def compile( s, flags, include_dirs, output_file, input_files ):
    ''' compile the Cpp wrapper and the verilated model into shared lib '''

    compile_cmd = 'g++ {flags} {idirs} -o {ofile} {ifiles}'

    compile_cmd = compile_cmd.format(
          flags     = flags, 
          idirs     = ' '.join( [ '-I'+d for d in include_dirs ] ), 
          ofile     = output_file, 
          ifiles    = ' '.join( input_files ), 
        )

    s.try_cmd( 'Compiling shared lib', compile_cmd )

  def generate_py_line_trace( s, m ):
    ''' create a line trace string for all ports '''

    ret = "'"   # eg: 'clk:{}, reset:{}, '.format( s.clk, s.reset, )

    for port in m.get_input_value_ports() | m.get_output_value_ports():
      ret += '{my_name}: {{}}, '.format( my_name = port._my_name )

    ret += "\\n'.format("

    for port in m.get_input_value_ports() | m.get_output_value_ports():
      ret += '{}, '.format( port._full_name )

    ret += ")"

    return ret

  def generate_py_internal_line_trace( s, m ):
    ''' create a line trace string for all ports inside the verilated
    model'''

    ret = "'"   # eg: 'clk:{}, reset:{}, '.format( s.clk, s.reset, )

    for port in m.get_input_value_ports() | m.get_output_value_ports():
      ret += '{my_name}: {{}}, '.format( my_name = port._my_name )

    ret += "\\n'.format("

    for port in m.get_input_value_ports() | m.get_output_value_ports():
      ret += '{}, '.format( 's._ffi_m.'+port._my_name+'[0]' )

    ret += ")"

    return ret
  
  def set_input_stmt( s, port ):
    ''' set up the interfaces between PyMTL and verilated model '''
    inputs = []
    for idx, offset in s.get_indices( port ):
      inputs.append( 's._ffi_m.{v_name}[{idx}] = s.{py_name}{offset}' \
          .format(
                v_name    = port.verilator_name,
                py_name   = port._my_name, 
                idx       = idx, 
                offset    = offset
            ) )
    return inputs

  def set_output_stmt( s, port ):
    ''' set up the interfaces between PyMTL and verilated model '''
    comb, next_ = [], []
    for idx, offset in s.get_indices( port ):
      stmt = 's.{py_name}{offset} = s._ffi_m.{v_name}[{idx}]'\
          .format(
                  v_name      = port.verilator_name, 
                  py_name     = port._my_name, 
                  idx         = idx, 
                  offset      = offset
              )
      comb.append( stmt )
      # next_.append( stmt )
    return comb, next_

  def get_indices( s, port ):
    ''' help determining assignment of wide ports '''
    num_assigns = 1 if port.Type.nbits <= 64 else (port.Type.nbits-1)/32+1
    if num_assigns == 1:
      return [(0, '')]
    return [( i, '[{}:{}]'.format( i*32, min( i*32+32, port.Type.nbits ) )
      ) for i in range(num_assigns)]

from pclib.rtl.arithmetics	import Adder

if __name__ == '__main__':
  m = Adder( Bits32 )
  m.elaborate()
  SimpleImportPass()( m, 'sum.v', 'Adder' )
  from test.trans_import.Adder_v import Adder as ImportedAdder
  import_m = ImportedAdder()
  import_m.elaborate()

#  import_m.reset = 0
  SimRTLPass()( import_m )
  print 'line trace: '+import_m.line_trace()
  print 'Internal line trace: '+import_m.internal_line_trace()
  import_m.unlock_simulation()
  import_m.reset = 0
  import_m.in0 = 0
  import_m.in1 = 0
  import_m.tick()
  print 'line trace: '+import_m.line_trace()
  print 'Internal line trace: '+import_m.internal_line_trace()

  import_m.reset = 0
  import_m.in0 = 1
  import_m.in1 = 2
  import_m.tick()
  print 'line trace: '+import_m.line_trace()
  print 'Internal line trace: '+import_m.internal_line_trace()

  import_m.reset = 1
  import_m.in0 = 23
  import_m.in1 = 21
  import_m.tick()
  print 'line trace: '+import_m.line_trace()
  print 'Internal line trace: '+import_m.internal_line_trace()

  for i in xrange(10):
    import_m.reset = 0
    import_m.in0 = i
    import_m.in1 = i+1 
    import_m.tick()
    print 'line trace: '+import_m.line_trace()
    print 'Internal line trace: '+import_m.internal_line_trace()
