#=========================================================================
# test_stateful
#=========================================================================
# Hypothesis stateful testing on RTL and CL model
#
# Author : Yixiao Zhang
#   Date : March 24, 2019

import inspect
import hypothesis.strategies as st
from pymtl import *
from hypothesis.stateful import *
from hypothesis import settings, given, seed, PrintSettings
from pymtl.dsl.test.sim_utils import simple_sim_pass
from test_wrapper import *

debug = True


def list_string( lst ):
  return ", ".join([ str( x ) for x in lst ] )


def list_string_value( lst ):
  str_list = []
  for x in lst:
    str_list += [ str( x ) ]
  return ", ".join( str_list )


#-------------------------------------------------------------------------
# MethodBasedRuleStrategy
#-------------------------------------------------------------------------
class MethodBasedRuleStrategy( SearchStrategy ):

  def __init__( self, machine ):
    SearchStrategy.__init__( self )
    self.machine = machine
    self.rules = machine.method_rules()

  def do_draw( self, data ):
    # This strategy draw a randomly selected number of rules and do not care about
    # validity. In execute_step(step), only valid rules will be fired. We do this to
    # test possible dependencies - some rules are not valid in the first place become
    # valid if some other rules fire in the same cycle
    n = len( self.rules )
    rule_to_fire = []
    if n > 0:
      remaining_rules = [ i for i in range( 0, n ) ]
      num_rules = cu.integer_range( data, 1, n )
      for _ in range( num_rules ):
        i = cu.integer_range( data, 0, len( remaining_rules ) - 1 )
        rule_to_fire += [ self.rules[ remaining_rules[ i ] ] ]
        del remaining_rules[ i ]

    if rule_to_fire:
      return [( rule, data.draw( rule.arguments_strategy ) )
              for rule in rule_to_fire ]


#-------------------------------------------------------------------------
# RunMethodTestError
#-------------------------------------------------------------------------
class RunMethodTestError( Exception ):
  pass


#-------------------------------------------------------------------------
# TestStateful
#-------------------------------------------------------------------------
class TestStateMachine( GenericStateMachine ):
  __argument_strategies = {}
  __preconditions = {}
  __method_rules = {}
  __always_rules = {}
  __condition_rules = {}

  def __init__( self ):
    super( TestStateMachine, self ).__init__()
    self.__rules_strategy = MethodBasedRuleStrategy( self )
    self.__stream = CUnicodeIO()
    self.__printer = RepresentationPrinter( self.__stream )
    self.__rtl_pending = {}
    self.__fl_pending = {}

    self.wrapper.reset()
    self.wrapper.tick()

  def _sim_cycle( self, method_line_trace="" ):
    #self.sim.cycle()
    print "{}  {}".format( self.sim.model.line_trace(), method_line_trace )

  def _error_line_trace( self, method_line_trace, error_msg ):
    self._sim_cycle( method_line_trace )
    #self.reference.cycle()
    print "========================== error =========================="
    raise RunMethodTestError( error_msg )

  def steps( self ):
    return self.__rules_strategy

  def execute_step( self, step ):

    self.wrapper.line_trace_string = ""
    for ruledata in step:
      rule, data = ruledata
      data = dict( data )

      # For dependency reason we do allow rules invalid in the first place
      # to be added to step.
      # See MethodBasedRuleStrategy for more
      if not self.is_valid( rule, data ):
        continue

      self.wrapper.rule_to_fire[ rule.method_name ] = data

    self.wrapper.tick()
    print self.wrapper.model.line_trace()

  def print_step( self, step ):
    print self.wrapper.model.line_trace()

  def is_valid( self, rule, data ):
    if rule.precondition and not rule.precondition( self, data ):
      return False
    return True

  @classmethod
  def add_argument_strategy( cls, method, arguments ):
    target = cls.__argument_strategies.setdefault( cls, {} )
    if target.has_key( method ):
      error_msg = """
      A method cannot have two distinct strategies. 
        method_name : {method_name}
      """.format( method_name=method )
      raise InvalidDefinition( error_msg )
    target[ method ] = arguments

  @classmethod
  def argument_strategy( cls, method ):
    target = cls.__argument_strategies.setdefault( cls, {} )
    return target.setdefault( method, {} )

  @classmethod
  def add_rule( cls, rules ):
    target = cls.__method_rules.setdefault( cls, [] )
    target += [ rules ]

  @classmethod
  def method_rules( cls ):
    target = cls.__method_rules.setdefault( cls, [] )
    return target

  @classmethod
  def add_precondition( cls, method, precondition ):
    target = cls.__preconditions.setdefault( cls, {} )
    target[ method ] = precondition

  @classmethod
  def precondition( cls, method ):
    target = cls.__preconditions.setdefault( cls, {} )
    return target.setdefault( method, None )


class TestStateful( TestStateMachine ):
  pass


class TestStatefulWrapper( ComponentLevel6 ):
  """
    #print s.model.method_specs
    @s.update
    def enq_test_stateful():
      if "enq" in s.rule_to_fire.keys():
        if s.model.enq.rdy():
          assert s.reference.enq.rdy()
          s.model.enq( **s.rule_to_fire[ "enq" ] )
          s.reference.enq( **s.rule_to_fire[ "enq" ] )
        else:
          assert not s.reference.enq.rdy()


    @s.update
    def deq_test_stateful():
      if "deq" in s.rule_to_fire.keys():
        if s.model.deq.rdy():
          assert s.reference.deq.rdy()
          msg1 = s.model.deq( **s.rule_to_fire[ "deq" ] )
          msg2 = s.reference.deq( **s.rule_to_fire[ "deq" ] )
          assert msg1 == msg2
        else:
          assert not s.reference.deq.rdy()
"""

  def construct( s, model, reference ):
    #s.test_stateful = test_stateful
    s.model = model
    s.reference = reference
    s.count = 0
    s.rule_to_fire = {}
    s.line_trace_string = ""

    for method, spec in s.model.method_specs.iteritems():
      filename = '<dynamic-123456>'
      updates = wrapper_tmpl.format( method=method )
      exec ( compile( updates, filename, 'exec' ), locals() )
      lines = [ line + '\n' for line in updates.splitlines() ]
      import linecache
      linecache.cache[ filename ] = ( len( updates ), None, lines, filename )

      rename( test_stateful, method + "_test_stateful" )
      s.update( test_stateful )

  def reset( s ):
    s.rule_to_fire = {}
    if hasattr( s.model, "reset" ):
      s.model.reset()
    if hasattr( s.reference, "reset" ):
      s.reference.reset()

  def line_trace( s ):
    return s.model.line_trace(), s.line_trace_string

  def done( s ):
    return False

  @staticmethod
  def _create_test_state_machine( model, reference, argument_strategy={} ):
    wrapper = TestStatefulWrapper( model, reference )
    wrapper.elaborate()
    wrapper.apply( simple_sim_pass )

    print wrapper._dsl.schedule

    method_specs = wrapper.model.method_specs

    Test = type(
        type( wrapper.model ).__name__ + "TestStateful_",
        TestStateful.__bases__, dict( TestStateful.__dict__ ) )

    for method, spec in method_specs.iteritems():
      arguments = {}
      if argument_strategy.has_key( method ) and isinstance(
          argument_strategy[ method ], ArgumentStrategy ):
        arguments = argument_strategy[ method ].arguments
      for arg, dtype in spec.args.iteritems():
        if not arguments.has_key( arg ):
          arguments[ arg ] = ArgumentStrategy.get_strategy_from_type( dtype )
          if not arguments[ arg ]:
            error_msg = """
  Argument strategy not specified!
    method name: {method_name}
    argument   : {arg}
"""
            raise RunMethodTestError(
                error_msg.format( method_name=method, arg=arg ) )
      Test.add_argument_strategy( method, arguments )
      Test.add_rule(
          MethodRule(
              method_name=method, arguments=arguments, precondition=None ) )

    Test.wrapper = wrapper
    Test.release_cycle_accuracy = False
    Test.method_specs = method_specs

    return Test


#-------------------------------------------------------------------------
# MethodRule
#-------------------------------------------------------------------------


@attr.s()
class MethodRule( object ):
  method_name = attr.ib()
  arguments = attr.ib()
  precondition = attr.ib()
  index = attr.ib( default=-1 )

  def __attrs_post_init__( self ):
    self.arguments_strategy = st.fixed_dictionaries( self.arguments )


#-------------------------------------------------------------------------
# ArgumentStrategy
#-------------------------------------------------------------------------
class ArgumentStrategy( object ):

  def __init__( s, **kwargs ):
    s.arguments = kwargs

  @staticmethod
  def bits_strategy( nbits ):
    return st.integers( min_value=0, max_value=( 1 << nbits ) - 1 )

  @staticmethod
  def value_strategy( range_value=None, start=0 ):
    return st.integers(
        min_value=start, max_value=range_value - 1 if range_value else None )

  @staticmethod
  def bitstruct_strategy( bitstruct, **kwargs ):

    @st.composite
    def strategy( draw ):
      new_bitstruct = bitstruct()
      for name, slice_ in type( bitstruct )._bitfields.iteritems():
        if not name in kwargs.keys():
          data = draw(
              ArgumentStrategy.bits_strategy( slice_.stop - slice_.start ) )
        else:
          data = draw( kwargs[ name ] )
        exec ( "new_bitstruct.{} = data".format( name ) ) in locals()
      return new_bitstruct

    return strategy()

  @staticmethod
  def bitstype_strategy( dtype ):
    if isinstance( dtype, Bits ):
      return ArgumentStrategy.bits_strategy( dtype.nbits )
    raise TypeError( "No supported bitstype strategy for {}".format(
        type( dtype ) ) )

  @staticmethod
  def get_strategy_from_type( dtype ):
    if isinstance( dtype, Bits ):
      return ArgumentStrategy.bitstype_strategy( dtype )
    if isinstance( dtype(), Bits ):
      return ArgumentStrategy.bitstype_strategy( dtype() )
    return None


#-------------------------------------------------------------------------
# ReferencePrecondition
#-------------------------------------------------------------------------
@attr.s()
class ReferencePrecondition( object ):
  precondition = attr.ib()


#-------------------------------------------------------------------------
# reference_precondition
#-------------------------------------------------------------------------
REFERENCE_PRECONDITION_MARKER = u'pymtl-method-based-precondition'


def reference_precondition( precond ):
  """Decorator to apply add precondition to an FL model, usually 
    enforces validity of datas

    For example::

        class TestFL:

            @precondition_fl( lambda machine, data: not data[ 'id' ] in machine.reference.snap_shot_free_list )
            def test_method_call( self, id ):
                ...
    """

  def accept( f ):
    existing_precondition = getattr( f, REFERENCE_PRECONDITION_MARKER, None )
    if existing_precondition is not None:
      raise InvalidDefinition(
          'A function cannot be used for two distinct preconditions.',
          Settings.default,
      )
    precondition = ReferencePrecondition( precondition=precond )

    @proxies( f )
    def precondition_wrapper(*args, **kwargs ):
      return f(*args, **kwargs )

    setattr( precondition_wrapper, REFERENCE_PRECONDITION_MARKER, precondition )
    return precondition_wrapper

  return accept


#-------------------------------------------------------------------------
# run_test_state_machine
#-------------------------------------------------------------------------
def run_test_state_machine( rtl_class,
                            reference_class,
                            argument_strategy={},
                            seed=None ):

  machine = TestStatefulWrapper._create_test_state_machine(
      rtl_class, reference_class )
  run_state_machine_as_test( machine )
