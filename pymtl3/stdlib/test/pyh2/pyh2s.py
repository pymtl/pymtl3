"""
==========================================================================
pyh2s.py
==========================================================================
PyH2S APIs for testing hardware as software.

Author : Yanghui Ou, Yixiao Zhang
  Date : July 9, 2019
"""
from copy import deepcopy

from hypothesis import HealthCheck, PrintSettings
from hypothesis import reproduce_failure as rf
from hypothesis import settings
from hypothesis.searchstrategy import SearchStrategy
from hypothesis.stateful import *

from pymtl3 import *
from pymtl3.datatypes import is_bitstruct_class
from pymtl3.datatypes import strategies as pst
from pymtl3.passes import AutoTickSimPass
from pymtl3.stdlib.cl.queues import NormalQueueCL
from pymtl3.stdlib.rtl.queues import NormalQueueRTL

from .RTL2CLWrapper import RTL2CLWrapper
from .utils import rename

#-------------------------------------------------------------------------
# BaseStateMachine
#-------------------------------------------------------------------------

class BaseStateMachine( RuleBasedStateMachine ):

  def __init__( s ):
    super( BaseStateMachine, s ).__init__()

    s.ref = deepcopy( s.preconstruct_ref )
    s.dut = deepcopy( s.preconstruct_dut )

    # Elaborate ref
    s.ref.apply( AutoTickSimPass() )
    s.ref.sim_reset()

    def wrap_line_trace( top ):
      func = top.line_trace

      top_level_callee_cl = top.get_all_object_filter(
        lambda x: isinstance(x, CalleeIfcCL) and x.get_host_component() is top )

      def line_trace():
        return "{} || {}".format( func(),
          " | ".join([ str(ifc) for ifc in top_level_callee_cl ])
        )
      top.line_trace = line_trace

    wrap_line_trace( s.dut )

    # Elaborate dut
    s.dut.apply( AutoTickSimPass() )
    s.dut.sim_reset()

    # Print header
    print("\n"+"="*74)
    print(" PyH2 trying examples...")
    print("="*74)

#-------------------------------------------------------------------------
# TestStateful
#-------------------------------------------------------------------------

try:
  from termcolor import colored
  termcolor_installed = True
except:
  termcolor_installed = False

class TestStateful( BaseStateMachine ):
  if termcolor_installed:
    def error_line_trace( self, error_msg="" ):
      print( colored("="*35 + " error " + "="*35, 'red') )
      print( colored(error_msg, 'red') )
      raise ValueError( error_msg )
  else:
    def error_line_trace( self, error_msg="" ):
      print( "="*35 + " error " + "="*35 )
      print( error_msg )
      raise ValueError( error_msg )

#-------------------------------------------------------------------------
# build_strategy_tree
#-------------------------------------------------------------------------
# Helper function that converts arg_strat_mapping into something easier to
# process. For example:
# { 'enq.msg' : pst.bits(16) } -> { 'enq': { 'msg' : pst.bits(16) } }
# Since bitstruct strategy accepts a json-like dictionary to specify min/max
# for each field, we just let the strategy handle the generated nested dict.

error_msg = """When setting strategy for {}:
- It seems like {} has already been specified as '{}'.
- Having strategy for a field and its subfield is not allowed."""

def build_strategy_tree( custom_strategies ):
  ret = {}

  if custom_strategies is None:
    return ret

  for full_name, strat in custom_strategies.items():
    if not isinstance( strat, (range, SearchStrategy) ):
      raise TypeError( f"Only strategy is allowed! Got {type(strat)} for {full_name}" )

    name = full_name.split( '.' )

    if len(name) < 2 or name[1] != 'msg':
      raise ValueError( f"We only accept '<method>.msg.xxx', not '{full_name}'" )

    cur = ret
    for i, x in enumerate(name):
      if not isinstance( cur, dict ):
        raise TypeError( error_msg.format( full_name, '.'.join(name[:i]), cur ) )

      if i == len(name) - 1:
        if x in cur:
          raise TypeError( error_msg.format( full_name, '.'.join(name[:i+1]), cur[x] ) )
        cur[x] = strat
      else:
        if x not in cur:
          cur[x] = {}
        cur = cur[x]
  return ret
#-------------------------------------------------------------------------
# mk_rule
#-------------------------------------------------------------------------
# make a rule from a method and its argument msg

ref_unwanted_ret_template = """
ref model has some problems in method '{name}':
  - ref didn't return None for method '{name}' without no return type
  - Instead, ref returned {ref_result}
"""

ref_invalid_ret_template = """
ref model has some problems in method '{name}':
  - ref didn't return '{RetType}' type of return value
  - Instead, ref returned {ref_result}
"""

dut_invalid_ret_template = """
dut has some problems in method '{name}':
  - dut didn't return '{RetType}' type of return value
  - Instead, dut returned {dut_result}
"""

mismatch_template = """
mismatch found in method {name}:
  - argument msg: {msg}
  - ref returned: {ref_result}
  - dut returned: {dut_result}
"""

def mk_rule( name, MsgType, RetType, custom_strategy_tree, cycle_accurate ):

  # Make a ready method for the state machine.

  if cycle_accurate:
    @rename( name + '_rdy' )
    def method_rdy( s ):
      dut_rdy = s.dut.__dict__[ name ].rdy()
      ref_rdy = s.ref.__dict__[ name ].rdy()

      if dut_rdy != ref_rdy:
        s.error_line_trace( f"""
mismatch found in method '{name}_rdy':
  - ref rdy: {ref_rdy}
  - dut rdy: {dut_rdy}
""" )
      return dut_rdy and ref_rdy
  else:
    # NOTE: Here we only call methods when both rdy returns true. Thus we
    # are only doing cycle-approximate or functional level testing.
    @rename( name + '_rdy' )
    def method_rdy( s ):
      dut_rdy = s.dut.__dict__[ name ].rdy()
      ref_rdy = s.ref.__dict__[ name ].rdy()
      return dut_rdy and ref_rdy

  # Make a rule for the state machine.
  # Now the arguments are passed in as a bitstruct

  if MsgType is None:
    if RetType is None:
      @precondition( lambda s: method_rdy( s ) )
      @rule() # FIXME
      @rename( name )
      def method_rule( s ):
        msg = None
        dut_result = s.dut.__dict__[ name ]()
        ref_result = s.ref.__dict__[ name ]()

        if ref_result is not None:
          s.error_line_trace( ref_unwanted_ret_template.format( **locals() ) )

        # TODO: allow using customized comparison function?
        if dut_result != ref_result:
          s.error_line_trace( mismatch_template.format( **vars() ) )
    else:
      @precondition( lambda s: method_rdy( s ) )
      @rule() # FIXME
      @rename( name )
      def method_rule( s ):
        msg = None
        dut_result = s.dut.__dict__[ name ]()
        ref_result = s.ref.__dict__[ name ]()

        # if not isinstance( ref_result, RetType ):
          # s.error_line_trace( ref_invalid_ret_template.format( **locals() ) )

        if not isinstance( dut_result, RetType ):
          s.error_line_trace( dut_invalid_ret_template.format( **locals() ) )

        # TODO: allow using customized comparison function?
        if dut_result != ref_result:
          s.error_line_trace( mismatch_template.format( **vars() ) )
  else:
    if is_bitstruct_class( MsgType ):
      if custom_strategy_tree is None:
        strategy = pst.bitstructs( MsgType )
      elif isinstance( custom_strategy_tree, SearchStrategy ):
        strategy = custom_strategy_tree
      else:
        # generate a bitstruct strategy including overwritten subtrees
        assert isinstance( custom_strategy_tree, dict )
        strategy = pst.bitstructs( MsgType, custom_strategy_tree )
    else:
      assert issubclass( MsgType, Bits )
      # Guaranteed by build_strategy_tree, strategy can only be range or
      # SearchStrategy
      strategy = custom_strategy_tree
      if strategy is None:
        strategy = pst.bits( MsgType.nbits )
      elif isinstance( strategy, range ):
        strategy = pst.bits( MsgType.nbits, min_value=strategy.start,
                                            max_value=strategy.stop-1 )
      if not isinstance( strategy, SearchStrategy ):
        raise TypeError( f"For '{MsgType.__name__}' field, only range/SearchStrategy can be accepted, " \
                         f"not '{strategy}'." )

    if RetType is None:
      @precondition( lambda s: method_rdy( s ) )
      @rule( msg = strategy ) # FIXME
      @rename( name )
      def method_rule( s, msg ):
        dut_result = s.dut.__dict__[ name ]( msg )
        ref_result = s.ref.__dict__[ name ]( msg )

        if ref_result is not None:
          s.error_line_trace( ref_unwanted_ret_template.format( **locals() ) )

        # TODO: allow using customized comparison function?
        if dut_result != ref_result:
          s.error_line_trace( mismatch_template.format( **vars() ) )
    else:
      @precondition( lambda s: method_rdy( s ) )
      @rule( msg = strategy )
      @rename( name )
      def method_rule( s, msg ):
        dut_result = s.dut.__dict__[ name ]( msg )
        ref_result = s.ref.__dict__[ name ]( msg )

        # if not isinstance( ref_result, RetType ):
          # s.error_line_trace( ref_invalid_ret_template.format( **locals() ) )

        if not isinstance( dut_result, RetType ):
          s.error_line_trace( dut_invalid_ret_template.format( **locals() ) )

        # TODO: allow using customized comparison function?
        if dut_result != ref_result:
          s.error_line_trace( mismatch_template.format( **vars() ) )

  return method_rule, method_rdy

#-------------------------------------------------------------------------
# create_test_state_machine
#-------------------------------------------------------------------------

def create_test_state_machine( dut, ref, custom_strategy=None, cycle_accurate=False ):
  Test = type( dut.model_name + "_StatefulPyH2", TestStateful.__bases__,
               dict( TestStateful.__dict__ ) )

  Test.preconstruct_dut = deepcopy( dut )
  Test.preconstruct_ref = deepcopy( ref )

  dut.elaborate()

  try:
    method_specs = dut.method_specs
  except AttributeError:
    raise f"No method specs specified in DUT {dut.model_name}. Did you wrap the RTL model?"

  assert method_specs, f"No top level CalleeIfcRTL found in DUT {dut.model_name}."

  # Process the custom strategy mapping and perform checks
  custom_strategy_tree = build_strategy_tree( custom_strategy )
  for name in custom_strategy_tree:
    assert name in method_specs, f"{name} is not a method-based interface for DUT."
    MsgType, _ = method_specs[ name ]
    if MsgType is None:
      raise TypeError(f"Custom strategy cannot be applied to method {name} that doesn't take any argument.")

  # Create two rules for each CalleeIfc
  for name, (MsgType, RetType) in method_specs.items():
    ifc_tree = custom_strategy_tree.get( name, {} ) # {} if no custom
    strat = ifc_tree.get( 'msg', None ) # {} if no custom

    method_rule, method_rdy = mk_rule( name, MsgType, RetType, strat, cycle_accurate )
    setattr( Test, name, method_rule )
    setattr( Test, name + "_rdy", method_rdy )

  return Test

#-------------------------------------------------------------------------
# run_pyh2s
#-------------------------------------------------------------------------
# Driver function for PyH2S. By default the strategies for each arg is
# inferred from the corresponding RTL port.
# TODO: figure out a way to pass in settings

def run_pyh2s( dut, ref, custom_strategy=None ):
  wrapped_dut = RTL2CLWrapper( dut )
  machine = create_test_state_machine( wrapped_dut, ref, custom_strategy )
  machine.TestCase.settings = settings(
    max_examples=50,
    stateful_step_count=100,
    deadline=None,
    # verbosity=Verbosity.verbose,
    database=None,
    suppress_health_check=[ HealthCheck.filter_too_much ],
  )

  run_state_machine_as_test( machine )
