#=========================================================================
# test_stateful
#=========================================================================
# Hypothesis stateful testing on RTL and CL model
#
# Author : Yixiao Zhang
#   Date : May 22, 2019

from __future__ import absolute_import, division, print_function

import hypothesis.strategies as st
from hypothesis import settings
from hypothesis.searchstrategy import SearchStrategy
from hypothesis.stateful import *

from pymtl3 import *
from pymtl3.passes import GenDAGPass, OpenLoopCLPass

from .test_wrapper import *


#-------------------------------------------------------------------------
# list_string
#-------------------------------------------------------------------------
def list_string( lst ):
  return ", ".join([ str( x ) for x in lst ] )


#-------------------------------------------------------------------------
# bitstype_strategy
#-------------------------------------------------------------------------
def bitstype_strategy( bits ):
  return st.integers( min_value=0, max_value=( 1 << bits.nbits ) - 1 )


#-------------------------------------------------------------------------
# bits_struct_strategy
#-------------------------------------------------------------------------
def bits_struct_strategy( bits_struct_type, all_field_st={} ):

  @st.composite
  def strategy( draw ):
    new_bits_struct = bits_struct_type()
    for name, field_type in bits_struct_type.fields:
      field_st = all_field_st.get( name, {} )
      # recursively draw st
      data = draw( get_strategy_from_type( field_type, field_st ) )
      setattr( new_bits_struct, name, data )
    return new_bits_struct

  return strategy()


#-------------------------------------------------------------------------
# get_strategy_from_type
#-------------------------------------------------------------------------
def get_strategy_from_type( dtype, all_field_st ):
  if isinstance( dtype(), Bits ):
    if all_field_st:
      assert isinstance(
          all_field_st,
          SearchStrategy ), "need strategy for Bits type {}, got {}".format(
              repr( dtype ), str( all_field_st ) )
      return all_field_st
    return bitstype_strategy( dtype() )
  if isinstance( dtype(), BitStruct ):
    return bits_struct_strategy( dtype, all_field_st )
  return None


#-------------------------------------------------------------------------
# BaseStateMachine
#-------------------------------------------------------------------------
class BaseStateMachine( RuleBasedStateMachine ):

  def __init__( s ):
    super( BaseStateMachine, s ).__init__()

    s.dut = deepcopy( s.preconstruct_dut )
    s.ref = deepcopy( s.preconstruct_ref )

    # elaborate dut
    s.dut.elaborate()
    s.dut.apply( GenDAGPass() )
    s.dut.apply( OpenLoopCLPass() )
    s.dut.lock_in_simulation()

    # elaborate ref
    s.ref.elaborate()
    s.ref.apply( GenDAGPass() )
    s.ref.apply( OpenLoopCLPass() )
    s.ref.lock_in_simulation()
    s.ref.hide_line_trace = True


#-------------------------------------------------------------------------
# TestStateful
#-------------------------------------------------------------------------
class TestStateful( BaseStateMachine ):

  def error_line_trace( self ):
    print( "============================= error ========================" )


#-------------------------------------------------------------------------
# wrap_method
#-------------------------------------------------------------------------
def wrap_method( method_spec, arguments ):
  method_name = method_spec.method_name

  @rename( method_name + "_rdy" )
  def method_rdy( s ):
    dut_rdy = s.dut.__dict__[ method_name ].rdy()
    ref_rdy = s.ref.__dict__[ method_name ].rdy()

    if dut_rdy and not ref_rdy:
      s.error_line_trace()
      raise ValueError( "Dut method is rdy but reference is not: " +
                        method_name )

    if not dut_rdy and ref_rdy:
      s.error_line_trace()
      raise ValueError( "Reference method is rdy but dut is not: " +
                        method_name )
    return dut_rdy

  @precondition( lambda s: method_rdy( s ) )
  @rule(**arguments )
  @rename( method_name )
  def method_rule( s, **kwargs ):
    dut_result = s.dut.__dict__[ method_name ](**kwargs )
    ref_result = s.ref.__dict__[ method_name ](**kwargs )

    if method_spec.rets_type:
      ref_result = method_spec.rets_type( ref_result )

    #compare results
    if dut_result != ref_result:
      s.error_line_trace()
      raise ValueError( """mismatch found in method {method}:
  - args: {data}
  - ref result: {ref_result}
  - dut result: {dut_result}
  """.format(
          method=method_name,
          data=list_string(
              [ "{k}={v}".format( k=k, v=v ) for k, v in kwargs.items() ] ),
          ref_result=ref_result,
          dut_result=dut_result ) )

  return method_rule, method_rdy


def get_strategy_from_list( st_list ):

  all_field_st = {}
  all_subfield_st = {}
  # First go through all customized strategy
  for name, st in st_list:
    field_name, subfield_name = name.split( ".", 1 )
    field_st = all_field_st.setdefault( field_name, {} )
    # strategy for a field
    if not "." in subfield_name:
      field_st[ subfield_name ] = st
    # strategy for subfield
    else:
      subfield_list = all_subfield_st.setdefault( field_name, [] )
      subfield_list += [( subfield_name, st ) ]

  for field_name, subfield_list in all_subfield_st.items():
    subfield_dict = get_strategy_from_list( subfield_list )
    for subfield in subfield_dict.keys():
      # a field with its strategy specified directly should not have
      # strategy for subfield. e.g. s.enq.msg and s.enq.msg.msg0 should
      # not be in st_list simultaneously
      assert not subfield in all_field_st
    all_field_st[ field_name ].update( subfield_dict )
  return all_field_st


#-------------------------------------------------------------------------
# create_test_state_machine
#-------------------------------------------------------------------------
def create_test_state_machine( dut,
                               ref,
                               method_specs=None,
                               argument_strategy={} ):
  Test = type( dut.model_name + "_TestStateful", TestStateful.__bases__,
               dict( TestStateful.__dict__ ) )

  Test.preconstruct_dut = deepcopy( dut )
  Test.preconstruct_ref = deepcopy( ref )

  dut.elaborate()

  if not method_specs:
    try:
      method_specs = dut.method_specs
    except Exception:
      raise "No method specs specified"

  # get customized strategy
  method_arg_st = get_strategy_from_list( argument_strategy )

  # go through spec for each method
  for method_name, spec in method_specs.iteritems():
    arg_st = method_arg_st.get( method_name, {} )

    # add the rest from inspection result
    for arg, dtype in spec.args:
      arg_st[ arg ] = get_strategy_from_type( dtype, arg_st.get( arg, {} ) )
      if not arg_st[ arg ]:
        error_msg = """
Argument strategy not specified!
  method name: {method_name}
  argument   : {arg}
"""
        raise ValueError( error_msg.format( method_name=method_name, arg=arg ) )

    method_rule, method_rdy = wrap_method( method_specs[ method_name ], arg_st )
    setattr( Test, method_name, method_rule )
    setattr( Test, method_name + "_rdy", method_rdy )

  return Test


#-------------------------------------------------------------------------
# run_test_state_machine
#-------------------------------------------------------------------------
def run_test_state_machine( dut, ref, argument_strategy={} ):

  machine = create_test_state_machine(
      dut, ref, argument_strategy=argument_strategy )
  machine.TestCase.settings = settings(
      max_examples=50,
      stateful_step_count=100,
      deadline=None,
      verbosity=Verbosity.verbose,
      database=None )
  run_state_machine_as_test( machine )
