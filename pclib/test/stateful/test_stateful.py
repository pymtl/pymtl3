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
from pymtl.passes.PassGroups import SimpleCLSim
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
    rule_to_fire.sort(
      key=lambda rule: (
        self.machine.order.index(rule.method_name),
        rule.index,
      )
    )

    if rule_to_fire:
      return [( rule, data.draw( rule.arguments_strategy ) )
              for rule in rule_to_fire ]


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
  __always_rules = {}
  __condition_rules = {}

  def __init__( self ):
    super( TestStateMachine, self ).__init__()
    self.__rules_strategy = MethodBasedRuleStrategy( self )
    self.__stream = CUnicodeIO()
    self.__printer = RepresentationPrinter( self.__stream )
    self.__rtl_pending = {}
    self.__fl_pending = {}

  def _sim_cycle( self, method_line_trace="" ):
    #self.sim.cycle()
    print "{}  {}".format( self.sim.model.line_trace(), method_line_trace )

  def _error_line_trace( self, method_line_trace, error_msg ):
    self._sim_cycle( method_line_trace )
    #self.reference.cycle()
    print "========================== error =========================="
    raise RunMethodTestError( error_msg )

  def _validate_result( self, m_ret_names, r_ret, method_name, arg,
                        method_line_trace ):
    type_error_msg = """
   Reference and model have mismatched returns!
    - method name    : {method_name}
    - model ret      : {model_ret}
    - reference ret  : {reference_ret}
  """
    if not r_ret:
      if m_ret_names:
        error_msg = type_error_msg.format(
            method_name=method_name,
            model_ret=list_string( m_ret_names ),
            reference_ret="" )
        self._error_line_trace( method_line_trace, error_msg )
      else:
        return

    r_ret_names = set( sorted( r_ret.keys() ) )
    if r_ret_names != m_ret_names:
      error_msg = type_error_msg.format(
          method_name=method_name,
          model_ret=list_string( m_ret_names ),
          reference_ret=list_string( r_ret_names ) )
      self._error_line_trace( method_line_trace, error_msg )

  def compare_result( self, m_result, r_result, method_name, arg,
                      method_line_trace ):
    r_result = r_result.__dict__
    m_result = m_result.__dict__

    #self._validate_result(m_ret_names, r_result, method_name, arg,
    #                      method_line_trace)

    value_error_msg = """
   test state machine received an incorrect value!
    - method name    : {method_name}
    - arguments      : {arg}
    - ret name       : {ret_name}
    - expected value : {expected_msg}
    - actual value   : {actual_msg}
  """

    for k in r_result.keys():
      if r_result[ k ] != '?' and not r_result[ k ] == m_result[ k ]:
        m_ret_names = set( sorted( m_result.keys() ) )
        m_result_list = [
            value for ( key, value ) in sorted( m_result.items() )
        ]
        r_result_list = [
            value for ( key, value ) in sorted( r_result.items() )
        ]
        error_msg = value_error_msg.format(
            method_name=method_name,
            arg=arg,
            ret_name=list_string( m_ret_names ),
            expected_msg=list_string_value( r_result_list ),
            actual_msg=list_string_value( m_result_list ) )
        self._error_line_trace( method_line_trace, error_msg )

  def steps( self ):
    return self.__rules_strategy

  def _call_func( s, model, name, data, index=-1 ):
    func = getattr( model, name )
    if index < 0:
      return func(**data )
    return func[ index ](**data )

  def _call_func_cl( s, model, name, data, index=-1 ):
    result = Result()
    rdy_func = model.__dict__[ name + "_rdy" ]
    if not rdy_func():
      result.rdy = 0
      return result
    func = model.__dict__[ name ]
    result.rdy = 1
    r = func(**data )
    if r != None:
      r = list(( r,) )
      ret_keys = s.method_specs[ name ].rets.keys()
      for i in range( len( ret_keys ) ):
        setattr( result, ret_keys[ i ], r[ i ] )
    return result

  def execute_step( self, step ):
    # store result of sim and reference
    s_results = []
    r_results = []
    method_names = []
    data_list = []

    method_line_trace = []
    # go though all rules for this step
    s_results_raw = []
    r_results_raw = []

    for ruledata in step:
      rule, data = ruledata
      data = dict( data )

      # For dependency reason we do allow rules invalid in the first place
      # to be added to step.
      # See MethodBasedRuleStrategy for more
      if not self.is_valid( rule, data ):
        continue

      data_list += [ data ]
      for k, v in list( data.items() ):
        if isinstance( v, VarReference ):
          data[ k ] = self.names_to_values[ v.name ]

      # For method based interface rules, call rdy ones only
      #methods = self.interface.methods
      method_name = rule.method_name
      index = rule.index

      s_results_raw += [ self._call_func( self.sim, method_name, data, index ) ]
      r_results_raw += [
          self._call_func_cl( self.reference, method_name, data )
      ]

    self.sim.cycle()
    self.reference.tick()

    for ruledata, s_result, r_result in zip( step, s_results_raw,
                                             r_results_raw ):
      rule, data = ruledata
      data = dict( data )

      method_name = rule.method_name
      index = rule.index

      if not s_result.rdy:
        if r_result.rdy:
          if self.release_cycle_accuracy:
            self.__rtl_pending_data[ method_name ] = data
            continue
          raise RunMethodTestError(
              "Reference model is rdy but RTL model is not: {}".format(
                  method_name ) )
        continue

      if not r_result.rdy:
        if self.release_cycle_accuracy:
          self.__fl_pending_data[ method_name ] = data
          continue
        raise RunMethodTestError(
            "RTL model is rdy but Reference is not: {}".format( method_name ) )

      # Method ready, add to result list
      method_names += [ method_name ]

      # If in debug mode, print out all the methods called
      if debug:
        argument_string = []
        for k, v in data.items():
          '''
          if isinstance(v, BitStruct):
            v = bitstruct_detail(v)'''
          argument_string += [ "{}={}".format( k, v ) ]
        index_string = "[{}]".format( index ) if index >= 0 else ""
        method_line_trace += [
            "{}{}( {} )".format( method_name, index_string,
                                 list_string( argument_string ) )
            if argument_string else "{}{}()".format( method_name, index_string )
        ]

      # Add to result list
      s_results += [ s_result ]
      r_results += [ r_result ]

    method_line_trace = ",  ".join( method_line_trace )

    # Compare results
    for s_result, r_result, method, data in zip( s_results, r_results,
                                                 method_names, data_list ):
      self.compare_result( s_result, r_result, method, data, method_line_trace )

    self._sim_cycle( method_line_trace )

  def print_step( self, step ):
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
  def _add_rule( cls, rules ):
    target = cls.__method_rules.setdefault( cls, [] )
    target += [ rules ]

  @classmethod
  def add_always_rule( cls, rules ):
    target = cls.__always_rules.setdefault( cls, [] )
    target += [ rules ]
    cls._add_rule( rules )

  @classmethod
  def add_condition_rule( cls, rules ):
    target = cls.__condition_rules.setdefault( cls, [] )
    target += [ rules ]
    cls._add_rule( rules )

  @classmethod
  def add_rule( cls, rules, hascall ):
    if hascall:
      cls.add_condition_rule( rules )
    else:
      cls.add_always_rule( rules )

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


#-------------------------------------------------------------------------
# Method
#-------------------------------------------------------------------------
@attr.s()
class Method( object ):
  method_name = attr.ib()
  args = attr.ib( default={} )
  rets = attr.ib( default={} )


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
  def array_strategy( dtype ):
    if not isinstance( dtype, Array ):
      raise TypeError( "No supported array strategy for {}".format(
          type( dtype ) ) )
    return st.lists(
        ArgumentStrategy.bitstype_strategy( dtype.Data ),
        min_size=dtype.length,
        max_size=dtype.length )

  @staticmethod
  def get_strategy_from_type( dtype ):
    if isinstance( dtype, Bits ) or isinstance( dtype, BitStruct ):
      return ArgumentStrategy.bitstype_strategy( dtype )
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
# TestStateful
#-------------------------------------------------------------------------
class TestStateful( TestStateMachine ):
  sim = None
  reference = None

  def __init__( self ):
    TestStateMachine.__init__( self )
    self.sim.reset()
    #self.reference.reset()

  @staticmethod
  def _run_state_machine( state_machine_factory ):
    run_state_machine_as_test( state_machine_factory )

  @staticmethod
  def inspect( rtl_class, cl_class ):
    rtl_class.apply( SimpleSim )
    cl_class.apply( SimpleCLSim )
    methods = {}
    method_specs = {}
    for method, ifc in inspect.getmembers( rtl_class ):
      if isinstance( ifc, Interface ):
        methods[ method ] = ifc.__dict__.copy()
        del methods[ method ][ "_dsl" ]
        del methods[ method ][ "en" ]
        del methods[ method ][ "rdy" ]

    for method, members in methods.iteritems():
      args, _, _, _ = inspect.getargspec( cl_class.__dict__[ method ].method )
      method_args = {}
      rets = methods[ method ]
      for arg in args[ 1:]:
        method_args[ arg ] = rets[ arg ]
        del rets[ arg ]
      method_specs[ method ] = Method(
          method_name=method, args=method_args, rets=rets )

    return method_specs

  @staticmethod
  def _create_test_state_machine( rtl_class,
                                  arg,
                                  cl_class,
                                  argument_strategy={},
                                  order=[],
                                  adapter=RTLAdapter,
                                  wrapper=RTLWrapper ):
    method_specs = TestStateful.inspect( rtl_class(*arg ), cl_class )
    rtl_class = wrapper( adapter( rtl_class(*arg ), method_specs ) )

    Test = type(
        type( rtl_class ).__name__ + "TestStateMachine_",
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
            raise RunMethodTestError(
                error_msg.format( method_name=name, arg=arg ) )
      Test.add_argument_strategy( method, arguments )
      Test.add_rule(
          MethodRule(
              method_name=method, arguments=arguments, precondition=None ),
          True )

    Test.sim = rtl_class
    Test.reference = cl_class
    Test.release_cycle_accuracy = False
    Test.order = order
    Test.method_specs = method_specs

    return Test


#-------------------------------------------------------------------------
# run_test_state_machine
#-------------------------------------------------------------------------
def run_test_state_machine( rtl_class,
                            arg,
                            reference_class,
                            argument_strategy={},
                            order=[],
                            seed=None,
                            adapter=RTLAdapter,
                            wrapper=RTLWrapper ):

  reference_class.apply( SimpleCLSim )
  state_machine_factory = TestStateful._create_test_state_machine(
      rtl_class,
      arg,
      reference_class,
      argument_strategy,
      order=order,
      adapter=adapter,
      wrapper=wrapper )

  if seed != None:
    state_machine_factory._hypothesis_internal_use_seed = seed
    state_machine_factory.TestCase.settings = settings(
        max_examples=50,
        deadline=None,
        verbosity=Verbosity.verbose,
        print_blob=PrintSettings.ALWAYS,
        database=None )
  else:
    state_machine_factory.TestCase.settings = settings(
        max_examples=50,
        deadline=None,
        verbosity=Verbosity.verbose,
        print_blob=PrintSettings.ALWAYS )
  TestStateful._run_state_machine( state_machine_factory )
