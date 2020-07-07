#=========================================================================
# test_utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 5, 2019
"""Provide utility methods for testing."""
import copy
from collections import deque

from hypothesis import strategies as st

from pymtl3.datatypes import Bits1, mk_bits
from pymtl3.dsl import OutPort
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.stdlib.test_utils import TestVectorSimulator

from ...yosys import YosysTranslationImportPass
from .. import VerilogTranslationImportPass

#=========================================================================
# test utility functions
#=========================================================================

def trim( s ):
  string = []
  lines = s.split( '\n' )
  for line in lines:
    _line = line.split()
    _string = "".join( _line )
    if _string and not _string.startswith( '//' ):
      string.append( "".join( line.split() ) )
  return "\n".join( string )

def check_eq( s, t ):
  if isinstance( s, list ) and isinstance( t, list ):
    for _s, _t in zip( s, t ):
      assert trim(_s) == trim(_t)
  else:
    assert trim(s) == trim(t)

#=========================================================================
# Hypothesis strategies for testing
#=========================================================================

def flatten( _rtype ):
  if isinstance( _rtype, rt.Array ):
    n_dim = _rtype.get_dim_sizes()
    rtype = _rtype.get_sub_type()
  else:
    n_dim = []
    rtype = _rtype
  return n_dim, rtype

#-------------------------------------------------------------------------
# Generate initialization data for a signal
#-------------------------------------------------------------------------

def VectorInitData( dtype ):
  nbits = dtype.get_length()
  min_val, max_val = -(2**(nbits-1)), 2**(nbits-1)-1
  value = 0
  return mk_bits( nbits )( value )

def StructInitData( dtype ):
  data = dtype.get_class()()
  for field_name, field in dtype.get_all_properties().items():
    setattr( data, field_name, DataTypeInitData( field ) )
  return data

def PackedArrayInitData( n_dim, sub_dtype ):
  if not n_dim:
    return DataTypeInitData( sub_dtype )
  else:
    data = []
    for i in range(n_dim[0]):
      data += [ PackedArrayInitData( n_dim[1:], sub_dtype ) ]
    return data

def DataTypeInitData( dtype ):
  if isinstance( dtype, rdt.Vector ):
    return VectorInitData( dtype )
  elif isinstance( dtype, rdt.Struct ):
    return StructInitData( dtype )
  elif isinstance( dtype, rdt.PackedArray ):
    n_dim = dtype.get_dim_sizes()
    sub_dtype = dtype.get_sub_dtype()
    return PackedArrayInitData( n_dim, sub_dtype )
  else:
    assert False, f"unrecognized data type {sub_dtype}!"

def InPortInitData( id_, port ):
  return { id_ : DataTypeInitData( port.get_dtype() ) }

def InterfaceInitData( id_, ifc ):
  init = {}
  for prop_name, prop_rtype in ifc.get_all_properties_packed():
    if isinstance( prop_rtype, rt.Array ):
      n_dim = prop_rtype.get_dim_sizes()
      sub_type = prop_rtype.get_sub_type()
      if isinstance(sub_type, rt.Port) and sub_type.get_direction() != "input":
        continue
      init.update( ArrayInitData( id_+"."+prop_name, n_dim, sub_type ) )
    elif isinstance( prop_rtype, rt.Port ):
      if prop_rtype.get_direction() == "input":
        init.update( InPortInitData( id_+"."+prop_name, prop_rtype ) )
    elif isinstance( prop_rtype, rt.InterfaceView ):
      init.update( InterfaceInitData( id_+"."+prop_name, prop_rtype ) )
  return init

def ArrayInitData( id_, n_dim, subtype ):
  if not n_dim:
    if isinstance( subtype, rt.Port ):
      return InPortInitData( id_, subtype )
    else:
      return InterfaceInitData( id_, subtype )
  else:
    init = {}
    for i in range(n_dim[0]):
      init.update( ArrayInitData(f'{id_}[{i}]', n_dim[1:], subtype) )
    return init

#-------------------------------------------------------------------------
# Hypothesis input data strategies
#-------------------------------------------------------------------------

@st.composite
def VectorDataStrategy( draw, dtype ):
  nbits = dtype.get_length()
  min_val, max_val = -(2**(nbits-1)), 2**(nbits-1)-1
  value = draw( st.integers( min_val, max_val ) )
  return mk_bits( nbits )( value )

@st.composite
def StructDataStrategy( draw, dtype ):
  data = dtype.get_class()()
  for field_name, field in dtype.get_all_properties().items():
    setattr( data, field_name, draw( DataTypeDataStrategy( field ) ) )
  return data

@st.composite
def PackedArrayDataStrategy( draw, n_dim, sub_dtype ):
  if not n_dim:
    return draw( DataTypeDataStrategy( sub_dtype ) )
  else:
    data = []
    for i in range(n_dim[0]):
      data += [ draw(PackedArrayDataStrategy( n_dim[1:], sub_dtype )) ]
    return data

@st.composite
def DataTypeDataStrategy( draw, dtype ):
  if isinstance( dtype, rdt.Vector ):
    return draw( VectorDataStrategy( dtype ) )
  elif isinstance( dtype, rdt.Struct ):
    return draw( StructDataStrategy( dtype ) )
  elif isinstance( dtype, rdt.PackedArray ):
    n_dim = dtype.get_dim_sizes()
    sub_dtype = dtype.get_sub_dtype()
    return draw( PackedArrayDataStrategy( n_dim, sub_dtype ) )
  else:
    assert False, f"unrecognized data type {sub_dtype}!"

@st.composite
def InPortDataStrategy( draw, id_, port ):
  return { id_ : draw(DataTypeDataStrategy( port.get_dtype() )) }

@st.composite
def InterfaceDataStrategy( draw, id_, ifc ):
  data = {}
  for prop_name, prop_rtype in ifc.get_all_properties_packed():
    if isinstance( prop_rtype, rt.Array ):
      n_dim = prop_rtype.get_dim_sizes()
      sub_type = prop_rtype.get_sub_type()
      if isinstance(sub_type, rt.Port) and sub_type.get_direction() != "input":
        continue
      data.update(draw(ArrayDataStrategy(id_+"."+prop_name, n_dim, sub_type)))
    elif isinstance( prop_rtype, rt.Port ):
      if prop_rtype.get_direction() == "input":
        data.update(draw(InPortDataStrategy(id_+"."+prop_name, prop_rtype)))
    elif isinstance( prop_rtype, rt.InterfaceView ):
      data.update(draw(InterfaceDataStrategy(id_+"."+prop_name, prop_rtype)))
  return data

@st.composite
def ArrayDataStrategy( draw, id_, n_dim, subtype ):
  if not n_dim:
    if isinstance( subtype, rt.Port ):
      return draw(InPortDataStrategy( id_, subtype ))
    else:
      return draw(InterfaceDataStrategy( id_, subtype ))
  else:
    data = {}
    for i in range(n_dim[0]):
      data.update(draw(
        ArrayDataStrategy(f'{id_}[{i}]', n_dim[1:], subtype)))
    return data

@st.composite
def DataStrategy( draw, dut ):
  """Return a strategy that generates input vector for component `dut`."""
  max_cycles = 10

  ret = []
  dut.elaborate()
  rifc = rt.RTLIRGetter(cache=False).get_component_ifc_rtlir( dut )
  ports = rifc.get_ports_packed()
  ifcs = rifc.get_ifc_views_packed()

  # Add reset cycle at the beginning
  reset1, reset2 = {}, {}
  for id_, port in ports:
    if id_ == "clk":
      reset1.update( { id_ : Bits1(0) } )
      reset2.update( { id_ : Bits1(1) } )
    elif id_ == "reset":
      reset1.update( { id_ : Bits1(1) } )
      reset2.update( { id_ : Bits1(1) } )
    else:
      n_dim, port_rtype = flatten( port )
      if port_rtype.get_direction() == "input":
        if n_dim:
          reset1.update( ArrayInitData( id_, n_dim, port_rtype ) )
          reset2.update( ArrayInitData( id_, n_dim, port_rtype ) )
        else:
          reset1.update( InPortInitData( id_, port_rtype ) )
          reset2.update( InPortInitData( id_, port_rtype ) )
  for id_, ifc in ifcs:
    n_dim, ifc_rtype = flatten( ifc )
    if n_dim:
      reset1.update( ArrayDataStrategy( id_, n_dim, ifc_rtype ) )
      reset2.update( ArrayDataStrategy( id_, n_dim, ifc_rtype ) )
    else:
      reset1.update( InterfaceInitData( id_, n_dim, ifc_rtype ) )
      reset2.update( InterfaceInitData( id_, n_dim, ifc_rtype ) )

  ret.append( reset1 )
  ret.append( reset2 )

  for i in range(max_cycles):
    data = {}
    for id_, port in ports:
      if id_ in [ "clk", "reset" ]:
        data.update( { id_ : Bits1(0) } )
      else:
        n_dim, port_rtype = flatten( port )
        if n_dim:
          if port_rtype.get_direction() == "input":
            data.update(draw( ArrayDataStrategy( id_, n_dim, port_rtype ) ))
        elif port_rtype.get_direction() == "input":
          data.update(draw( InPortDataStrategy( id_, port_rtype ) ))
    for id_, ifc in ifcs:
      n_dim, ifc_rtype = flatten( ifc )
      if n_dim:
        data.update(draw( ArrayDataStrategy( id_, n_dim, ifc_rtype ) ))
      else:
        data.update(draw( InterfaceDataStrategy( id_, ifc_rtype ) ))

    # Toggle clock signal
    toggle_data = {}
    for id_, signal in data.items():
      if id_ == "clk":
        toggle_data.update( { id_ : Bits1(1) } )
      else:
        toggle_data.update( { id_ : copy.deepcopy( signal ) } )

    ret.append( data )
    ret.append( toggle_data )

  return ret

#-------------------------------------------------------------------------
# closed_loop_component_input_test
#-------------------------------------------------------------------------

def closed_loop_component_input_test( dut, test_vector, tv_in, backend = "verilog" ):

  # Filter to collect all output ports of a component
  def outport_filter( obj ):
    return isinstance( obj, OutPort )

  assert backend in [ "verilog", "yosys" ], f"invalid backend {backend}!"

  dut.elaborate()
  reference_output = deque()
  all_output_ports = dut.get_local_object_filter( outport_filter )

  # Method to record reference outputs of the pure python component
  def ref_tv_out( model, test_vector ):
    dct = {}
    for out_port in all_output_ports:
      dct[ out_port ] = eval( "model." + out_port._dsl.my_name ).clone() # WE NEED TO CLONE NOW
    reference_output.append( dct )

  # Method to compare the outputs of the imported model and the pure python one
  def tv_out( model, test_vector ):
    assert len(reference_output) > 0, \
      "Reference runs for fewer cycles than the imported model!"
    for out_port in all_output_ports:
      ref = reference_output[0][out_port]
      imp = eval( "model." + out_port._dsl.my_name )
      assert ref == imp, f"Value mismatch: reference: {ref}, imported: {imp}"
    reference_output.popleft()

  # First simulate the pure python component to see if it has sane behavior
  reference_sim = TestVectorSimulator( dut, test_vector, tv_in, ref_tv_out )
  reference_sim.run_test()
  dut.unlock_simulation()

  # If it simulates correctly, translate it and import it back
  dut.elaborate()
  if backend == "verilog":
    dut.set_metadata( VerilogTranslationImportPass.enable, True )
    imported_obj = VerilogTranslationImportPass()( dut )
  elif backend == "yosys":
    dut.set_metadata( YosysTranslationImportPass.enable, True )
    imported_obj = YosysTranslationImportPass()( dut )

  # Run another vector simulator spin
  imported_sim = TestVectorSimulator( imported_obj, test_vector, tv_in, tv_out )
  imported_sim.run_test()

#-------------------------------------------------------------------------
# closed_loop_component_test
#-------------------------------------------------------------------------

def closed_loop_component_test( dut, data, backend = "verilog" ):
  """Test the DUT with the given test_vector.

  User who wish to use this method should pass in the hypothesis data
  strategy instance as `data`. This method will reflect on the interfaces
  and ports of the given DUT and generate input vector.
  """
  # Method to feed data into the DUT
  def tv_in( model, test_vector ):
    for name, data in test_vector.items():
      # `setattr` fails to set the correct value of an array if indexed by
      # a subscript. We use `exec` here to make sure the value of elements
      # are assigned correctly.
      exec( "model." + name + " @= data" )
  test_vector = data.draw( DataStrategy( dut ) )
  closed_loop_component_input_test( dut, test_vector, tv_in, backend )

#-------------------------------------------------------------------------
# closed_loop_test
#-------------------------------------------------------------------------

# TODO: A hypothesis test that works on generated test component AND
# generated input data.
def closed_loop_test():
  pass
