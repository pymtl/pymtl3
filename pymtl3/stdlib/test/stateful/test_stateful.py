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
# ArgumentStrategy
#-------------------------------------------------------------------------
class ArgumentStrategy( object ):

  def __init__( s, **kwargs ):
    s.arguments = kwargs


#-------------------------------------------------------------------------
# bitstype_strategy
#-------------------------------------------------------------------------
def bitstype_strategy( dtype ):
  if isinstance( dtype, Bits ):
    return st.integers( min_value=0, max_value=( 1 << dtype.nbits ) - 1 )
  raise TypeError( "No supported bitstype strategy for {}".format(
      type( dtype ) ) )


#-------------------------------------------------------------------------
# get_strategy_from_type
#-------------------------------------------------------------------------
def get_strategy_from_type( dtype ):
  if isinstance( dtype, Bits ):
    return bitstype_strategy( dtype )
  if isinstance( dtype(), Bits ):
    return bitstype_strategy( dtype() )
  return None


#-------------------------------------------------------------------------
# BaseStateMachine
#-------------------------------------------------------------------------
class BaseStateMachine( RuleBasedStateMachine ):

  def __init__( s ):
    super( BaseStateMachine, s ).__init__()

    s.dut = deepcopy( s.preconstruct_model )
    s.ref = deepcopy( s.preconstruct_reference )

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


#-------------------------------------------------------------------------
# create_test_state_machine
#-------------------------------------------------------------------------
def create_test_state_machine( model,
                               reference,
                               method_specs=None,
                               argument_strategy={} ):
  Test = type( model.model_name + "_TestStateful", TestStateful.__bases__,
               dict( TestStateful.__dict__ ) )

  Test.preconstruct_model = deepcopy( model )
  Test.preconstruct_reference = deepcopy( reference )

  model.elaborate()

  if not method_specs:
    try:
      method_specs = model.method_specs
    except Exception:
      raise "No method specs specified"

  # go through spec for each method
  for method_name, spec in method_specs.iteritems():
    arguments = {}
    # First add customized arguments
    if method_name in argument_strategy and isinstance(
        argument_strategy[ method_name ], ArgumentStrategy ):
      arguments = argument_strategy[ method_name ].arguments

    # add the rest from inspection result
    for arg, dtype in spec.args.iteritems():
      if arg not in arguments:
        arguments[ arg ] = get_strategy_from_type( dtype )
        if not arguments[ arg ]:
          error_msg = """
  Argument strategy not specified!
    method name: {method_name}
    argument   : {arg}
"""
          raise RunMethodTestError(
              error_msg.format( method_name=method_name, arg=arg ) )

    method_rule, method_rdy = wrap_method( method_specs[ method_name ],
                                           arguments )
    setattr( Test, method_name, method_rule )
    setattr( Test, method_name + "_rdy", method_rdy )

  return Test


#-------------------------------------------------------------------------
# run_test_state_machine
#-------------------------------------------------------------------------
def run_test_state_machine( rtl_class, reference_class, argument_strategy={} ):

  machine = create_test_state_machine( rtl_class, reference_class )
  machine.TestCase.settings = settings(
      max_examples=50,
      stateful_step_count=100,
      deadline=None,
      verbosity=Verbosity.verbose,
      database=None )
  run_state_machine_as_test( machine )
