"""
==========================================================================
stateful.py
==========================================================================
PyH2 APIs for stateful testing.

Author : Yanghui Ou, Yixiao Zhang
  Date : July 9, 2019
"""
from __future__ import absolute_import, division, print_function

import inspect
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

from ..stateful.test_wrapper import Method
from .RTL2CLWrapper import RTL2CLWrapper
from .utils import kwarg_to_str, list_string, method_to_str, rename

try:
  from termcolor import colored
  termcolor_installed = True
except:
  termcolor_installed = False

#-------------------------------------------------------------------------
# collect_mspecs
#-------------------------------------------------------------------------
# TODO: organize these into a pass?

def collect_mspecs( dut ):
  method_specs = {}

  for method_name, ifc in inspect.getmembers( dut ):
    if isinstance( ifc, Interface ):
      assert hasattr( ifc, '_mspec' ), "Cannot wrap {}! Method spec is not specified!".format( ifc._dsl.my_name )

      # Yanghui : do we need args and rets to be ordered?
      args = []
      if ifc._mspec.arg is not None:
        for port_name, port_type in ifc._mspec.arg.iteritems():
          args.append( (port_name, port_type) )

      rets = []
      if ifc._mspec.ret is not None:
        for port_name, port_type in ifc._mspec.ret.iteritems():
          rets.append( (port_name, port_type) )

      method_specs[ method_name ] = Method( method_name, args, rets )

  return method_specs

#-------------------------------------------------------------------------
# mk_rule
#-------------------------------------------------------------------------
# make a rule from a method and its spec

def mk_rule( method_spec, arg_strat_dict ):
  method_name = method_spec.method_name

  # Make a ready method for the state machine.
  # NOTE: we only call methods when both rdy returns true. Thus we are only
  # doing cycle-approximate or functional level testing.
  @rename( method_name + '_rdy' )
  def method_rdy( s ):
    dut_rdy = s.dut.__dict__[ method_name ].rdy()
    ref_rdy = s.ref.__dict__[ method_name ].rdy()
    return dut_rdy and ref_rdy

  # Make a rule for the state machine.
  # NOTE: now the CL arg must be the same as the corresponding RTL port
  # name. We should find a way to figure out the mapping between the RTL
  # port and method arg.
  @precondition( lambda s: method_rdy( s ) )
  @rule( **arg_strat_dict )
  @rename( method_name )
  def method_rule( s, **kwargs ):
    dut_result = s.dut.__dict__[ method_name ]( **kwargs )
    ref_result = s.ref.__dict__[ method_name ]( **kwargs )

    # Compare results
    # TODO: allow using customized comparison function?
    if dut_result != ref_result:

      error_msg = """
mismatch found in method {method}:
  - args: {args}
  - ref result: {ref_result}
  - dut result: {dut_result}
""".format(
        method=method_name,
        args=kwarg_to_str( kwargs ),
        ref_result=ref_result,
        dut_result=dut_result,
      )

      s.error_line_trace( error_msg )

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

# TODO: clean this up
def get_strategy_from_list( st_list ):
  # Generate a nested dictionary for customized strategy
  # e.g. [ ( 'enq.msg', st1 ), ('deq.msg.msg0', st2 ) ]
  # turns into {
  #  'enq': { 'msg': st1 },
  #  'deq': { 'msg': { 'msg0': st2 } }
  # }
  all_field_st = {}
  all_subfield_st = {}

  # First go through all customized strategy,
  # Create a dict of ( field, [ ( subfield, strategy ) ] ) for non-leaf
  # Create a dict of ( field, strategy ) for leaf
  for name, st in st_list:
    field_name, subfield_name = name.split( ".", 1 )
    field_st = all_field_st.setdefault( field_name, {} )
    # leaf
    if not "." in subfield_name:
      field_st[ subfield_name ] = st

    # non-leaf
    else:
      subfield_list = all_subfield_st.setdefault( field_name, [] )
      subfield_list += [( subfield_name, st ) ]

  # Recursively generate dict for subfields
  for field_name, subfield_list in all_subfield_st.items():
    subfield_dict = get_strategy_from_list( subfield_list )
    for subfield in subfield_dict.keys():
      # If a field has a customized strategy, there should not be any
      # strategy for its subfields. e.g. s.enq.msg and s.enq.msg.msg0 should
      # not be in st_list simultaneously
      field_st = all_field_st[ field_name ]
      assert not subfield in field_st.keys(), (
          "Found customized strategy for {}. "
          "Separate strategy for its fields are not allowed".format(
              field_st[ subfield ][ 1 ] ) )
    all_field_st[ field_name ].update( subfield_dict )
  return all_field_st

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
    else:
      ret[method_name][arg_name] = strat

  return ret


#-------------------------------------------------------------------------
# create_test_state_machine
#-------------------------------------------------------------------------

def create_test_state_machine(
  dut,
  ref,
  method_specs=None,
  arg_strat_mapping={},
):
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

  # Process the arg_strat_mapping
  m_arg_strat_dict = parse_arg_strat_mapping( arg_strat_mapping )

  # Go through spec for each method
  for method_name, spec in method_specs.items():
    if method_name not in m_arg_strat_dict:
      arg_strat = {}
    else:
      arg_strat = m_arg_strat_dict[ method_name ]

    # create strategy based on types and predefined customization
    for arg, Type in spec.args:
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

def run_pyh2( dut, ref, arg_strat_mapping={} ):
  new_dut = deepcopy( dut )
  new_dut.elaborate()
  method_specs = collect_mspecs( new_dut )
  wrapped_dut = RTL2CLWrapper( dut, method_specs )
  machine = create_test_state_machine( wrapped_dut, ref, method_specs, arg_strat_mapping )
  machine.TestCase.settings = settings(
    max_examples=50,
    stateful_step_count=100,
    deadline=None,
    # verbosity=Verbosity.verbose,
    database=None,
    suppress_health_check=[ HealthCheck.filter_too_much ],
  )

  run_state_machine_as_test( machine )

def test_pyh2():
  run_pyh2(
    dut=NormalQueueRTL( Bits16, num_entries=2 ),
    ref=NormalQueueCL( num_entries=2 ),
    arg_strat_mapping = {
      'enq.msg' : pst.bits(16, signed=True)
    }
  )
