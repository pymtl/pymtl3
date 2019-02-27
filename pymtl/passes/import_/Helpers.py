#=========================================================================
# Helpers.py
#=========================================================================
# This file includes the functions that might be useful to some import
# passes. Some of the functions are based on PyMTL v2.
# 
# Author : Peitian Pan
# Date   : Feb 22, 2019

from pymtl.passes.Helpers import make_indent
from pymtl.passes.rast    import get_type

#-------------------------------------------------------------------------
# generate_signal_decl_c
#-------------------------------------------------------------------------

def generate_signal_decl_c( name, port ):

  type_str = get_type( port ).type_str()

  nbits = type_str[ 'nbits' ]

  if    nbits <= 8:  data_type = 'unsigned char'
  elif  nbits <= 16: data_type = 'unsigned short'
  elif  nbits <= 32: data_type = 'unsigned int'
  elif  nbits <= 64: data_type = 'unsigned long'
  else:              data_type = 'unsigned int'

  return '{data_type} * {name}{c_dim_size};'.format(
    data_type = data_type, name = name,
    c_dim_size = type_str[ 'c_dim_size' ]
  )

#-------------------------------------------------------------------------
# generate_signal_init_c
#-------------------------------------------------------------------------

def generate_signal_init_c( name, port ):

  ret = []

  type_str = get_type( port ).type_str()

  nbits     = type_str[ 'nbits' ]
  deference = '&' if nbits <= 64 else ''

  if type_str[ 'c_dim_size' ] != '':
    # This is a potentially recursive array structure
    n_dim_size = type_str[ 'n_dim_size' ]

    subscript_str = ''

    for idx, dim_size in enumerate( n_dim_size ):
      ret.append( 'for ( int i_{idx} = 0; i_{idx} < {dim_size}; i_{idx}++ )'.format(
        idx = idx, dim_size = dim_size
      ) )
      subscript_str += '[i_{idx}]'.format( idx = idx )

    ret.append( 'm->{name}{sub} = {deference}model->{name}{sub};'.format(
      name = name, deference = deference, sub = subscript_str
    ) )

    # Indent the whole for loop appropriately

    for start, dim_size in enumerate( n_dim_size ):
      for idx in xrange( start+1, len( n_dim_size )+1 ):
        ret[ idx ] = '  ' + ret[ idx ]

  else:
    ret.append( 'm->{name} = {deference}model->{name};'.format( **locals() ) )

  return ret

#-------------------------------------------------------------------------
# load_ssg
#-------------------------------------------------------------------------
# Return the sensitivity group from the given .ssg file. None is returned
# if the given ssg file does not exist.

def load_ssg( ssg_name ):

  def parse_css( css ):
    """Parse a comma-separated string and return a list of all fields"""
    return map( lambda x: x.strip(), css.split( ',' ) )

  try:
    with open( ssg_name, 'r' ) as ssg_file:

      ssg = []
      for line in ssg_file:
        ssg_rule = line.strip().replace( '\n', '' )
        pos = line.find( '=>' )

        if pos == -1:
          raise Exception( '.ssg file does not have the correct format!' )

        in_ports  = ssg_rule[ : pos ].strip()
        out_ports = ssg_rule[ pos+2 : ].strip()

        ssg.append( ( parse_css( out_ports ), parse_css( in_ports ) ) )

  except IOError:
    ssg = None

  return ssg

#-------------------------------------------------------------------------
# generate_default_ssg
#-------------------------------------------------------------------------
# Generate the default ssg from the given module interface. Assume all
# outport ports depends on all input ports (both combinationally and
# sequentially).

def generate_default_ssg( ports ):

  inports, outports = [], []

  for port in ports:
    if   isinstance( port, InVPort ):   inports.append( port._dsl.my_name )
    elif isinstance( port, OutVPort ): outports.append( port._dsl.my_name )

  return [ ( outports, map( lambda x: 'B'+x, inports ) ) ]

#-------------------------------------------------------------------------
# generate_signal_decl_py
#-------------------------------------------------------------------------

def generate_signal_decl_py( name, port ):

  type_str = get_type( port ).type_str()

  nbits = type_str[ 'nbits' ]
  dtype_str = type_str[ 'py_type' ]

  ret = '{}'

  if type_str[ 'c_dim_size' ] != '':
    n_dim_size = type_str[ 'n_dim_size' ]

    for idx, dim_size in enumerate( n_dim_size ):
      ret = ret.format( '[{{}} for i_{idx} in xrange({size})]'.format(
        idx = idx, size = dim_size
      ) )

  ret = ret.format( dtype_str+'(Bits'+str(nbits)+')' )
  ret = 's.' + name + ' = ' + ret

  return ret

#-------------------------------------------------------------------------
# generate_seq_upblk_py
#-------------------------------------------------------------------------

def generate_seq_upblk_py( ports, ssg ):

  seq_upblk_tplt = """@s.update_on_edge
    def tick_sequential():
{register_inputs}
      s._ffi_m.clk[0] = 0
      s._ffi_inst.eval( s._ffi_m )
      s._ffi_m.clk[0] = 1
      s._ffi_inst.eval( s._ffi_m )"""

  seq_in_ports = set()
  port_objs = {}
  seq_dep_outports = set()

  for port in ports: port_objs[ port._dsl.my_name ] = port

  # C: there is only combinational path from the input to the output
  # S: there is only sequential path from the input to the output
  # B: there are both seq and comb path from the input to the output
  for idx, (out, in_) in enumerate( ssg ):
    for in_port in in_:
      if in_port.startswith( ('S', 'B') ):
        seq_in_ports.add( in_port[1:] )
        seq_dep_outports.add( idx )

  # Purely combinational models do not need sequential blocks
  if len( seq_in_ports ) == 0: return '', []

  set_inputs = []
  constraints = []

  # Generate input assignments and constraints

  for in_port in seq_in_ports:
    for idx, offset in get_indices( port_objs[ in_port ] ):
      set_inputs.append( 's._ffi_m.{name}[{idx}] = s.{name}{offset}'.format(
        name = in_port, idx = idx, offset = offset
      ) )

    constraints.append( 'U(tick_sequential) < WR(s.{}),'.format( in_port ) )

  make_indent( set_inputs, 3 )

  for outport in seq_dep_outports:
    constraints.append( 'U(tick_sequential) < U(readout_{}),'.format( outport ) )

  # Fill in the seq upblk template

  seq_upblk = seq_upblk_tplt.format( register_inputs = '\n'.join( set_inputs ) )

  return seq_upblk, constraints

#-------------------------------------------------------------------------
# generate_comb_upblks_py
#-------------------------------------------------------------------------
# Return a list of comb upblks in string.

def generate_comb_upblks_py( ports, ssg ):

  comb_upblk_tplt = """
    @s.update
    def comb_eval_{idx}():
      # set inputs
{set_inputs}
      # call evaluate function
      s._ffi_inst.eval( s._ffi_m )"""

  comb_ssg = []
  port_objs = {}

  for port in ports: port_objs[ port._dsl.my_name ] = port

  # C: there is only combinational path from the input to the output
  # S: there is only sequential path from the input to the output
  # B: there are both seq and comb path from the input to the output
  for idx, (out, in_) in enumerate( ssg ):
    inports = []

    for in_port in in_:
      if in_port.startswith( ('C', 'B') ):
        inports.append( in_port[1:] )

    if len( inports ) != 0:
      comb_ssg.append( ( inports, out, idx ) )

  # Purely sequential models do not need combinational blocks
  if len( comb_ssg ) == 0: return '', []

  # Generate a list of comb upblks according to comb_ssg

  comb_upblks = []
  constraints = []

  for inports, outports, upblk_num in comb_ssg:
    set_inputs = []

    for in_port in inports:
      for idx, offset in get_indices( port_objs[ in_port ] ):
        set_inputs.append( 's._ffi_m.{name}[{idx}] = s.{name}{offset}'.format(
          name = in_port, idx = idx, offset = offset
        ) )

      constraints.append( 'U(comb_eval_{idx}) < WR(s.{name}),'.format(
        idx = upblk_num, name = in_port
      ) )

    make_indent( set_inputs, 3 )

    constraints.append( 'U(comb_eval_{idx}) < U(readout_{idx}),'.format(
      idx = upblk_num
    ) )

    # Fill in the comb upblk template

    comb_upblk = comb_upblk_tplt.format(
      idx = upblk_num, set_inputs = '\n'.join( set_inputs )
    )

    comb_upblks.append( comb_upblk )

  return comb_upblks, constraints

#-------------------------------------------------------------------------
# generate_readout_upblks_py
#-------------------------------------------------------------------------

def generate_readout_upblks_py( ports, ssg ):

  readout_upblks = []
  port_objs = {}
  constraints = []

  for port in ports: port_objs[ port._dsl.my_name ] = port

  readout_tplt = """
    @s.update
    def readout_{idx}():
      {read_outputs}"""

  for upblk_num, ( out, in_ ) in enumerate( ssg ):
    read_outputs = []

    for outport in out:
      for idx, offset in get_indices( port_objs[ outport ] ):
        read_outputs.append( 's.{name}{offset} = s._ffi_m.{name}[{idx}]'.format(
          name = outport, offset = offset, idx = idx
        ) )

        constraints.append( 'U(readout_{idx}) < RD(s.{name}),'.format(
          idx = upblk_num, name = outport
        ) )

    readout_upblk = readout_tplt.format(
      idx = upblk_num, read_outputs = '\n'.join( read_outputs )
    )

    readout_upblks.append( readout_upblk )

  return readout_upblks, constraints

#-------------------------------------------------------------------------
# generate_line_trace_py
#-------------------------------------------------------------------------
# A line trace that shows the value of all PyMTL wrapper ports

def generate_line_trace_py( ports ):

  ret = "'"

  for port in ports:
    ret += '{my_name}: {{}}, '.format( my_name = port._dsl.my_name )

  ret += "'.format("

  for port in ports:
    ret += '{}, '.format( port._dsl.full_name )

  ret += ")"

  return ret

#-------------------------------------------------------------------------
# generate_internal_line_trace_py
#-------------------------------------------------------------------------
# A line trace that shows the value of all cffi ports

def generate_internal_line_trace_py( ports ):

  ret = "'"

  for port in ports:
    ret += '{my_name}: {{}}, '.format( my_name = port._dsl.my_name )

  ret += "\\n'.format("

  for port in ports:
    ret += '{}, '.format( 's._ffi_m.'+port._dsl.my_name+'[0]' )

  ret += ")"

  return ret

#-------------------------------------------------------------------------
# get_indices
#-------------------------------------------------------------------------
# Generate a list of idx-offset tuples to copy data from verilated
# model to PyMTL model.

def get_indices( port ):

  type_str = get_type( port ).type_str()

  nbits = type_str[ 'nbits' ]

  num_assigns = 1 if nbits <= 64 else (nbits-1)/32+1

  if num_assigns == 1:
    return [(0, '')]

  return [
    ( i, '[{}:{}]'.format( i*32, min( i*32+32, nbits ) ) ) \
    for i in range(num_assigns)
  ]
