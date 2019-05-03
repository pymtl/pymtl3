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
import copy
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
    if n > 0:
      i = cu.integer_range( data, 0, n - 1 )
      rule = self.rules[ i ]
      return ( rule, data.draw( rule.arguments_strategy ) )
    raise ValueError( "No rule in state machine" )


#-------------------------------------------------------------------------
# RunMethodTestError
#-------------------------------------------------------------------------
class RunMethodTestError( Exception ):
  pass


#-------------------------------------------------------------------------
# TestStateMachine
#-------------------------------------------------------------------------
class TestStateMachine( GenericStateMachine ):
  __argument_strategies = {}
  __preconditions = {}
  __method_rules = {}

  def __init__( self ):
    super( TestStateMachine, self ).__init__()
    self.__rules_strategy = MethodBasedRuleStrategy( self )
    self.__stream = CUnicodeIO()
    self.__printer = RepresentationPrinter( self.__stream )
    self.model = copy.deepcopy( self.preconstruct_model )
    self.reference = copy.deepcopy( self.preconstruct_reference )

    self.model.elaborate()
    self.model.apply( simple_sim_pass )
    self.model.sim_reset()
    self.reference.elaborate()
    self.reference.apply( simple_sim_pass )

  def steps( self ):
    return self.__rules_strategy

  def error_line_trace( self ):
    print "============================= error ========================"
    print self.model.line_trace(), self.line_trace_string

  def execute_step( self, step ):

    self.line_trace_string = ""
    rule, data = step
    data = dict( data )

    # For dependency reason we do allow rules invalid in the first place
    # to be added to step.
    # See MethodBasedRuleStrategy for more
    method_name = rule.method_name
    if self.model.__dict__[ method_name ].rdy(
    ) and not self.reference.__dict__[ method_name ].rdy():
      self.error_line_trace()
      raise ValueError(
          "Dut method is rdy but reference is not: {method_name}".format(
              method_name=method_name ) )
    if not self.model.__dict__[ method_name ].rdy(
    ) and self.reference.__dict__[ method_name ].rdy():
      self.error_line_trace()
      raise ValueError(
          "Reference method is rdy but dut is not: {method_name}".format(
              method_name=method_name ) )
    if self.model.__dict__[ method_name ].rdy(
    ) and self.reference.__dict__[ method_name ].rdy():
      m_result = self.model.__dict__[ method_name ](**data )
      r_result = self.reference.__dict__[ method_name ](**data )
      self.line_trace_string += method_name + "(" + ", ".join([
          "{arg}={value}".format( arg=arg, value=value )
          for arg, value in data.iteritems()
      ] ) + ")"

      if r_result:
        self.line_trace_string += " --> " + str(r_result)

      if not m_result == r_result:
        self.error_line_trace()
        raise ValueError( """mismatch found in method {method}:
  - args: {data}
  - reference result: {r_result}
  - model result : {m_result}
  """.format(
            method=method_name,
            data=str( data ),
            r_result=r_result,
            m_result=m_result ) )

    self.model.tick()
    self.reference.tick()

    print self.model.line_trace(), self.line_trace_string

  def print_step( self, step ):
    """Print a step to the current reporter.

    This is called right before a step is executed.
    """
    pass

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


def create_test_state_machine( model, reference, argument_strategy={} ):
  Test = type(
      type( model ).__name__ + "TestStateful_", TestStateful.__bases__,
      dict( TestStateful.__dict__ ) )

  Test.preconstruct_model = copy.deepcopy( model )
  Test.preconstruct_reference = copy.deepcopy( reference )

  model.elaborate()

  method_specs = model.method_specs

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

  Test.method_specs = method_specs

  return Test


#-------------------------------------------------------------------------
# run_test_state_machine
#-------------------------------------------------------------------------
def run_test_state_machine( rtl_class,
                            reference_class,
                            argument_strategy={},
                            seed=None ):

  machine = create_test_state_machine( rtl_class, reference_class )
  machine.TestCase.settings = settings(
      max_examples=50,
      deadline=None,
      verbosity=Verbosity.verbose,
      database=None )
  run_state_machine_as_test( machine )
