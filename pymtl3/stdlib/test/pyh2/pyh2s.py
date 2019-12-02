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
from pymtl3.datatypes import strategies as pst
from pymtl3.passes import GenDAGPass, OpenLoopCLPass
from pymtl3.passes.sverilog import ImportPass
from pymtl3.stdlib.cl.queues import NormalQueueCL
from pymtl3.stdlib.rtl.queues import NormalQueueRTL

from .RTL2CLWrapper import RTL2CLWrapper
from .utils import list_string, rename

try:
  from termcolor import colored
  termcolor_installed = True
except:
  termcolor_installed = False

#-------------------------------------------------------------------------
# mk_rule
#-------------------------------------------------------------------------
# make a rule from a method and its argument msg

def mk_rule( name, ifc, MsgType, RetType ):
  method_name = method_name

  # Make a ready method for the state machine.
  # NOTE: we only call methods when both rdy returns true. Thus we are only
  # doing cycle-approximate or functional level testing.

  @rename( method_name + '_rdy' )
  def method_rdy( s ):
    dut_rdy = s.dut.__dict__[ method_name ].rdy()
    ref_rdy = s.ref.__dict__[ method_name ].rdy()
    return dut_rdy and ref_rdy

  # Make a rule for the state machine.
  # Now the arguments are passed in as a bitstruct
  @precondition( lambda s: method_rdy( s ) )
  @rule( **arg_strat_dict ) # FIXME
  @rename( method_name )
  def method_rule( s, msg ):
    dut_result = s.dut.__dict__[ method_name ]( msg )
    ref_result = s.ref.__dict__[ method_name ]( msg )
    assert isinstance( ref_result, RetType ), f"ref is wrong; it didn't return {RetType} type of ret, but {ref_result} instead."

    # Compare results
    # TODO: allow using customized comparison function?
    if dut_result != ref_result:
      s.error_line_trace( f"""
mismatch found in method {method_name}:
  - argument msg: {args}
  - ref returned: {ref_result}
  - dut returned: {dut_result}
""" )

  return method_rule, method_rdy

#-------------------------------------------------------------------------
# infer_strategy_from_type
#-------------------------------------------------------------------------
# TODO: added a default strategy for arbitrary bit struct as well?

def infer_strategy_from_type( dtype ):

  # We only support Bits at the moment.
  if isinstance( dtype(), Bits ):
    return pst.bits( dtype.nbits )

  raise TypeError( "Argument strategy for {} not supported".format( dtype ) )

#-------------------------------------------------------------------------
# BaseStateMachine
#-------------------------------------------------------------------------

class BaseStateMachine( RuleBasedStateMachine ):

  def __init__( s ):
    super( BaseStateMachine, s ).__init__()

    s.dut = deepcopy( s.preconstruct_dut )
    s.ref = deepcopy( s.preconstruct_ref )

    def wrap_line_trace( top ):
      func = top.line_trace

      def line_trace():
        return "{} || {}".format(
          func(),
          " | ".join([ method_to_str(ifc) for ifc in top.top_level_nb_ifcs ])
        )
      top.line_trace = line_trace

    wrap_line_trace( s.dut )

    # Elaborate dut
    s.dut.elaborate()
    s.dut = ImportPass()( s.dut )
    s.dut.elaborate()
    s.dut.apply( GenDAGPass() )
    s.dut.apply( OpenLoopCLPass() )
    s.dut.lock_in_simulation()
    s.dut.sim_reset()

    # Elaborate ref
    s.ref.elaborate()
    s.ref.hide_line_trace = True
    s.ref.apply( GenDAGPass() )
    s.ref.apply( OpenLoopCLPass() )
    s.ref.lock_in_simulation()
    s.ref.sim_reset()

    # Print header
    print("\n"+"="*74)
    print(" PyH2 trying examples...")
    print("="*74)

#-------------------------------------------------------------------------
# TestStateful
#-------------------------------------------------------------------------

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
# parse_arg_strat_mapping
#-------------------------------------------------------------------------
# Helper function that converts arg_strat_mapping into something easier to
# process. For example:
# { 'enq.msg' : pst.bits(16) } -> { 'enq': { 'msg' : pst.bits(16) } }
# For now, we don't support just specifying one field of a bit struct. A
# strategy for bit struct must be passed in as whole.

def parse_arg_strat_mapping( arg_strat_mapping ):
  ret = {}
  for name, strat in arg_strat_mapping.items():
    method_name, arg_name = name.split( '.', 1 )
    assert '.' not in arg_name
    if method_name not in ret:
      ret[ method_name ] = { arg_name : strat }


#-------------------------------------------------------------------------
# create_test_state_machine
#-------------------------------------------------------------------------

def create_test_state_machine( dut, ref ):
  Test = type( dut.model_name + "_StatefulPyH2", TestStateful.__bases__,
               dict( TestStateful.__dict__ ) )

  Test.preconstruct_dut = deepcopy( dut )
  Test.preconstruct_ref = deepcopy( ref )

  dut.elaborate()

  for name, strat in arg_strat_mapping.items():
    # Sanity check
    if not isinstance( strat, SearchStrategy ):
      raise TypeError(
        "Only strategy is allowed! Got {} for {}".format( type( strat ), name )
      )

  try:
    method_specs = dut.method_specs
  except Exception:
    raise "No method specs specified. Did you wrap the RTL model?"

  # Store ( strategy, full_name )
  arg_st_with_full_name = []
  all_st_full_names = set()
  for name, st in argument_strategy:

    if not isinstance( st, SearchStrategy ):
      raise TypeError( "Only strategy is allowed! got {} for {}".format(
          type( st ), name ) )

  # Process the arg_strat_mapping
  m_arg_strat_dict = parse_arg_strat_mapping( arg_strat_mapping )

  # Go through spec for each method
  for method_name, spec in method_specs.items():
    if method_name not in m_arg_strat_dict:
      arg_strat = {}
    else:
      arg_strat = m_arg_strat_dict[ method_name ]

  # go through spec for each method
  for method_name, (MsgType, RetType) in method_specs.iteritems():
    if MsgType is not None:

    arg_st = method_arg_st.get( method_name, {} )

    # create strategy based on types and predefined customization
    for arg, Type in spec.args:
      if arg not in arg_strat:
        arg_strat[ arg ] = infer_strategy_from_type( Type )

    # wrap method
    method_rule, method_rdy = mk_rule( spec, arg_strat )
    setattr( Test, method_name, method_rule )
    setattr( Test, method_name + "_rdy", method_rdy )

  return Test

#-------------------------------------------------------------------------
# run_pyh2
#-------------------------------------------------------------------------
# Driver function for PyH2. By default the strategies for each arg is
# inferred from the corresponding RTL port.
# TODO: figure out a way to pass in settings
# TODO: figure out a way to pass in customized strategies

def run_pyh2s( dut, ref ):
  wrapped_dut = RTL2CLWrapper( dut )
  machine = create_test_state_machine( wrapped_dut, ref )
  machine.TestCase.settings = settings(
    max_examples=50,
    stateful_step_count=100,
    deadline=None,
    # verbosity=Verbosity.verbose,
    database=None,
    suppress_health_check=[ HealthCheck.filter_too_much ],
  )

  run_state_machine_as_test( machine )
