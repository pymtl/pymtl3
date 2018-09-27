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
import re
import sys
import shutil

from pymtl          import *
from BasePass       import BasePass
from subprocess     import check_output, STDOUT, CalledProcessError
from errors         import VerilatorCompileError, PyMTLImportError
from SimRTLPass     import SimRTLPass

# Better indention

tab2 = '\n  '
tab4 = '\n    '
tab6 = '\n      '
tab8 = '\n        '

class SimpleImportPass( BasePass ):

  def __call__( s, model ):
    """ Import a Verilog/SystemVerilog file. model is the PyMTL source of
        the input verilog file. """

    # model should have been translated

    try:
      assert model._translated, "SimpleImportPass() only works on\
      translated components!"
    except AttributeError:
      raise PyMTLImportError( 'ImportPass: the model should be translated!' )

    # Assume the input verilog file has the same name as the class of
    # model
    
    verilog_file = model.__class__.__name__

    # Assume the top module of the input file has the same name as the 
    # class of model

    top_module   = model.__class__.__name__

    # Get all ports

    ports = model.get_input_value_ports() | model.get_output_value_ports()
    
    # Generate Verilog and verilator names for all ports

    for port in ports:
      port.verilog_name   = s.generate_verilog_name( port._my_name )
      port.verilator_name = s.generate_verilator_name( port.verilog_name )
      if '[' in port._my_name:
        port.verilog_name = get_array_name( port.verilog_name )
        port.verilator_name = get_array_name( port.verilator_name )
		
    # Compile verilog_file with verilator

    s.create_verilator_model( verilog_file, top_module )

    # Create a cpp wrapper for the verilated model

    model.array_dict, port_cdef, c_wrapper = s.create_verilator_c_wrapper( model,\
        top_module ) 

    # Compile the cpp wrapper and the verilated model into a shared lib

    lib_file = s.create_shared_lib( model, c_wrapper, top_module )

    # Create a python wrapper that can access the verilated model

    py_wrapper_file = s.create_verilator_py_wrapper( model, top_module, 
                                lib_file, port_cdef, model.array_dict )

    py_wrapper = py_wrapper_file.split('.')[0]

    if py_wrapper in sys.modules:
      # We are in a repeatedly running test process
      # Reloading is needed since user may have updated the source file
      exec( "reload( sys.modules[ '{py_wrapper}' ] )".format( **locals() ) )
      exec( "ImportedModel = sys.modules[ '{py_wrapper}' ].{top_module}".\
            format( **locals() )
          )
    else:
      # First time execution
      import_cmd = \
        'from {py_wrapper} import {top_module} as ImportedModel'.\
            format( py_wrapper = py_wrapper, 
                    top_module = top_module,
                )

      exec( import_cmd )

    model.imported_model = ImportedModel()

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

    # Collect all array ports
    
    array_dict = {}

    ports = sorted( model.get_input_value_ports() |\
                    model.get_output_value_ports(), key = repr )

    s.collect_array_ports( array_dict, ports )

    # Generate input and output ports for the verilated model

    port_externs = []
    port_cdef = []

    for port in ports:
      # Only generate an array port decl if index is zero
      if '[' in port._my_name and get_array_idx( port._my_name ) != 0:
        continue
      port_externs.append( s.port_to_decl( array_dict, port ) + tab4 )
      port_cdef.append( s.port_to_decl( array_dict, port ) )

    port_externs = ''.join( port_externs )

    # Generate initialization stmts for in/out ports

    port_inits = []

    for port in ports:
      # Generate n array port assignment if index is zero
      if '[' in port._my_name and get_array_idx( port._my_name ) != 0:
        continue
      port_inits.extend(
          map( lambda x: x + tab2, s.port_to_init( array_dict, port ) )
          )

    port_inits = ''.join( port_inits )

    with open( template_file, 'r' ) as template, \
         open( verilator_c_wrapper_file, 'w' ) as output:

          c_wrapper = template.read()
          c_wrapper = c_wrapper.format( top_module    = top_module,
                                        port_externs  = port_externs, 
                                        port_inits    = port_inits,
                                      )
          output.write( c_wrapper )

    return array_dict, port_cdef, verilator_c_wrapper_file

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

  def create_verilator_py_wrapper( s, model, top_module, lib_file,\
      port_cdef, array_dict ):
    ''' create a python wrapper that can manipulate the verilated model
    through the interfaces exposed by Cpp wrapper '''

    template_file = os.path.dirname( os.path.abspath( __file__ ) ) + \
                    os.path.sep + 'verilator_wrapper_template.py'

    verilator_py_wrapper_file = top_module + '_v.py'

    # Port definitions for verilated model

    port_externs  = ''.join( x+tab8 for x in port_cdef )

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

    # Create PyMTL port definitions, input setting, comb stmts

    for port in model.get_input_value_ports():
      name = port._my_name
      if '[' in name:
        if get_array_idx( name ) != 0:
          continue
        else:
          # Only create definition for the element of index 0
          nbits = port.Type.nbits
          array_range = array_dict[ get_array_name( name ) ]
          name = get_array_name( name )
          port_defs.append( '''s.{name} = [ InVPort(Bits{nbits}) '''
                            '''for _x in xrange({array_range}) ]'''\
                            .format( **locals() ) 
              )
      else:
        # This port is not a list
        port_defs.append( '{name} = InVPort( Bits{nbits} )'.format(
            name = port._full_name, 
            nbits = port.Type.nbits,
          ) )
      if port._my_name == 'clk':
        continue
      # Generate assignments to setup the inputs of verilated model 
      set_inputs.extend( s.set_input_stmt( port, array_dict ) )

    for port in model.get_output_value_ports():
      name = port._my_name
      if '[' in name:
        if get_array_idx( name ) != 0:
          continue
        else:
          # Only create definition for the element of index 0
          nbits = port.Type.nbits
          array_range = array_dict[ get_array_name( name ) ]
          name = get_array_name( name )
          port_defs.append( '''s.{name} = [ OutVPort(Bits{nbits})'''
                            ''' for _x in xrange({array_range}) ]'''\
                            .format( **locals() ) 
              )
      else:
        # This port is not a list
        port_defs.append( '{name} = OutVPort( Bits{nbits} )'.format(
            name = port._full_name, 
            nbits = port.Type.nbits,
          ) )
      # Generate assignments to read output from the verilated model
      comb, next_ = s.set_output_stmt( port, array_dict )
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
        cmd     = e.cmd, 
        error   = e.output
      ) )

  def collect_array_ports( s, array_dict, ports ):
    """ fill array_dict with port names and ranges """
    for port in ports:
      if '[' in port._my_name:
        array_name    = get_array_name( port._my_name )
        array_idx     = get_array_idx( port._my_name )
        try: 
          array_range = array_dict[ array_name ]
        except KeyError:
          array_range = 1
        array_dict[ array_name ] = max( array_idx + 1, array_range )

  def port_to_decl( s, array_dict, port ):
    """ generate port declarations for port """

    if '[' in port._my_name:
      # port belongs to a list of ports
      ret         = '{data_type} * {name}[{array_range}];'
      name        = get_array_name( port._my_name )
      array_range = array_dict[ name ]
    else:
      # single port
      ret         = '{data_type} * {name};'
      name        = port._my_name

    bitwidth = port.Type.nbits

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

  def port_to_init( s, array_dict, port ):
    """ generate port initializations for port """

    ret = []
    
    bitwidth       = port.Type.nbits
    dereference    = '&' if bitwidth <= 64 else ''

    if '[' in port._my_name:
      name = get_array_name( port._my_name )
      ret.append( 'for( int i = 0; i < {array_range}; i++ )'.format(\
            array_range = array_dict[ name ]
          ))
      ret.append( '  m->{name}[i] = {dereference}model->{name}[i];'.\
          format( name = name, dereference = dereference ) )
    else:
      name = port._my_name
      ret.append( 'm->{name} = {dereference}model->{name};'.\
          format( name = name, dereference = dereference ) )

    return ret

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

    ret = "'"   # eg: 'clk:{}, reset:{}, \n'.format( s.clk, s.reset, )

    ports = sorted(
        m.get_input_value_ports() | m.get_output_value_ports(), 
        key = repr
        )

    for port in ports:
      ret += '{my_name}: {{}}, '.format( my_name = port._my_name )

    ret += "'.format("

    for port in ports:
      ret += '{}, '.format( port._full_name )

    ret += ")"

    return ret

  def generate_py_internal_line_trace( s, m ):
    ''' create a line trace string for all ports inside the verilated
    model'''

    ret = "'"   # eg: 'clk:{}, reset:{}, \n'.format( s.clk, s.reset, )

    ports = sorted(
        m.get_input_value_ports() | m.get_output_value_ports(), 
        key = repr
        )

    for port in ports:
      ret += '{my_name}: {{}}, '.format( my_name = port._my_name )

    ret += "\\n'.format("

    for port in ports:
      ret += '{}, '.format( 's._ffi_m.'+port._my_name+'[0]' )

    ret += ")"

    return ret
  
  def set_input_stmt( s, port, array_dict ):
    ''' generate initializations for interfaces '''
    inputs = []
    name = port._my_name
    if '[' in name:
      # special treatment for list
      name = get_array_name( name )
      inputs.append( 'for _x in xrange({array_range}):'.format(
            array_range = array_dict[ name ]
        ) )
      for idx, offset in s.get_indices( port ):
        inputs.append('  s._ffi_m.{v_name}[_x][{idx}]=s.{py_name}[_x]{offset}'.\
                format( v_name      = port.verilator_name, 
                        py_name     = name, 
                        idx         = idx, 
                        offset      = offset
                      ) )
    else:
      for idx, offset in s.get_indices( port ):
        inputs.append( 's._ffi_m.{v_name}[{idx}] = s.{py_name}{offset}'.\
                format(
                        v_name    = port.verilator_name,
                        py_name   = name, 
                        idx       = idx, 
                        offset    = offset
                      ) )
    return inputs

  def set_output_stmt( s, port, array_dict ):
    ''' generate the list of vars that should be called in update blocks or
    update-on-edge blocks'''
    comb, next_ = [], []
    outputs = []
    name = port._my_name
    if '[' in name:
      name = get_array_name( name )
      outputs.append( 'for _x in xrange({array_range}):'.format(
            array_range = array_dict[ name ]
        ) )
      for idx, offset in s.get_indices( port ):
        outputs.append('  s.{py_name}[_x]{offset} = s._ffi_m.{v_name}[_x][{idx}]'\
            .format(
                    v_name      = port.verilator_name, 
                    py_name     = name, 
                    idx         = idx, 
                    offset      = offset
                  ) )
    else:
      for idx, offset in s.get_indices( port ):
        stmt = 's.{py_name}{offset} = s._ffi_m.{v_name}[{idx}]'\
            .format(
                    v_name      = port.verilator_name, 
                    py_name     = port._my_name, 
                    idx         = idx, 
                    offset      = offset
                )
      outputs.append( stmt )
      # next_.append( stmt )

    comb = outputs
    # FIXME: which type of update block does this variable come from?
    # next_ = outputs
    return comb, next_

  def get_indices( s, port ):
    ''' help determining assignment of wide ports '''
    num_assigns = 1 if port.Type.nbits <= 64 else (port.Type.nbits-1)/32+1
    if num_assigns == 1:
      return [(0, '')]
    return [( i, '[{}:{}]'.format( i*32, min( i*32+32, port.Type.nbits ) )
      ) for i in range(num_assigns)]

#-------------------------------------------------------------------------------
# Global helper functions
#-------------------------------------------------------------------------------

def get_array_name( name ):
  return re.sub( r'\[(\d+)\]', '', name )

def get_array_idx( name ):
  m = re.search( r'\[(\d+)\]', name )
  return int( m.group( 1 ) )
