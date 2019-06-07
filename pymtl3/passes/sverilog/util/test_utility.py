#=========================================================================
# test_utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 5, 2019
"""Provide utility methods for testing."""

from __future__ import absolute_import, division, print_function

from collections import deque

import hypothesis.strategies as st

from pymtl3.datatypes import mk_bits
from pymtl3.dsl import OutPort
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog import ImportPass, TranslationPass
from pymtl3.stdlib.test import TestVectorSimulator

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
  all_properties = dtype.get_all_properties()
  for field_name, field in all_properties:
    setattr( data, field_name, draw(
      DataTypeDataStrategy( field ) ) )
  return data

@st.composite
def PackedArrayDataStrategy( draw, n_dim, sub_dtype ):
  if not n_dim:
    return draw( DataTypeDataStrategy( sub_dtype ) )
  else:
    data = []
    for i in xrange(n_dim[0]):
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
    assert False, "unrecognized data type {}!".format( sub_dtype )

@st.composite
def InPortDataStrategy( draw, id_, port ):
  return { id_ : draw(DataTypeDataStrategy( port.get_dtype() )) }

@st.composite
def InterfaceDataStrategy( draw, id_, ifc ):
  data = {}
  all_properties = ifc.get_all_properties_packed()
  for prop_name, prop_rtype in all_properties:
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
    for i in xrange(n_dim[0]):
      data.update(draw(
        ArrayDataStrategy(id_+'[{}]'.format(i), n_dim[1:], subtype)))
    return data

@st.composite
def DataStrategy( draw, dut ):
  """Return a strategy that generates input vector for component `dut`."""
  max_cycles = 10

  ret = []
  dut.elaborate()
  rifc = rt.get_component_ifc_rtlir( dut )
  ports = rifc.get_ports_packed()
  ifcs = rifc.get_ifc_views_packed()
  for i in xrange(max_cycles):
    data = {}
    for id_, port in ports:
      if isinstance( port, rt.Array ):
        if port.get_sub_type().get_direction() == "input":
          n_dim = port.get_dim_sizes()
          port_rtype = port.get_sub_type()
          data.update(draw( ArrayDataStrategy( id_, n_dim, port_rtype ) ))
      elif port.get_direction() == "input":
        data.update(draw( InPortDataStrategy( id_, port ) ))
    for id_, ifc in ifcs:
      if isinstance( ifc, rt.Array ):
        n_dim = port.get_dim_sizes()
        ifc_rtype = ifc.get_sub_type()
        data.update(draw( ArrayDataStrategy( id_, n_dim, ifc_rtype ) ))
      else:
        data.update(draw( InterfaceDataStrategy( id_, ifc ) ))
    ret.append( data )
  return ret

#-------------------------------------------------------------------------
# closed_loop_component_input_test
#-------------------------------------------------------------------------

def closed_loop_component_input_test( dut, test_vector, tv_in ):

  # Filter to collect all output ports of a component
  def outport_filter( obj ):
    return isinstance( obj, OutPort )

  dut.elaborate()
  reference_output = deque()
  all_output_ports = dut.get_local_object_filter( outport_filter )

  # Method to record reference outputs of the pure python component
  def ref_tv_out( model, test_vector ):
    dct = {}
    for out_port in all_output_ports:
      dct[ out_port ] = getattr( model, out_port._dsl.my_name )
    reference_output.append( dct )

  # Method to compare the outputs of the imported model and the pure python one
  def tv_out( model, test_vector ):
    assert len(reference_output) > 0, \
      "Reference runs for fewer cycles than the imported model!"
    for out_port in all_output_ports:
      ref = reference_output[0][out_port]
      imp = getattr( model, out_port._dsl.my_name )
      assert ref == imp, \
        "Value mismatch: reference: {}, imported: {}".format( ref, imp )
    reference_output.popleft()

  # First simulate the pure python component to see if it has sane behavior
  reference_sim = TestVectorSimulator( dut, test_vector, tv_in, ref_tv_out )
  reference_sim.run_test()
  dut.unlock_simulation()

  try:
    # If it simulates correctly, translate it and import it back
    dut.elaborate()
    dut._sverilog_translate = True
    dut._sverilog_import = True
    dut.apply( TranslationPass() )
    imported_obj = ImportPass()( dut )
    # Run another vector simulator spin
    imported_sim = TestVectorSimulator( imported_obj, test_vector, tv_in, tv_out )
    imported_sim.run_test()
  finally:
    try:
      # Explicitly finalize the imported object because the shared lib may have
      # name collison
      imported_obj.finalize()
    except UnboundLocalError:
      # This test fails before the object is imported back
      pass

#-------------------------------------------------------------------------
# closed_loop_component_test
#-------------------------------------------------------------------------

def closed_loop_component_test( dut, test_vector ):
  """Test the DUT with the given test_vector.
  
  User who wish to use this method should generate the test vector from
  data.draw( DataStrategy( dut ) ) ( `data` is a hypothesis strategy that 
  allows you to draw examples in the body of a test ), which allows hypothesis
  to shrink the generated test vector when the test fails.
  """
  # Method to feed data into the DUT
  def tv_in( model, test_vector ):
    for name, data in test_vector.iteritems():
      setattr( model, name, data )
  closed_loop_component_input_test( dut, test_vector, tv_in )

#-------------------------------------------------------------------------
# closed_loop_test
#-------------------------------------------------------------------------

def closed_loop_test():
  pass
