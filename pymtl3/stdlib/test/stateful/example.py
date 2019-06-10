#=========================================================================
# example
#=========================================================================
# manual coded xample for test_stateful and test_wrapper
#
# Author : Yixiao Zhang
#   Date : June 10, 2019

from __future__ import absolute_import, division, print_function

import hypothesis.strategies as st
from hypothesis import Verbosity, settings
from hypothesis.stateful import *

from pymtl3 import *
from pymtl3.passes import GenDAGPass, OpenLoopCLPass

from .test_stateful_queues_test import BypassQueueCL, SingleEntryBypassQueue
from .test_wrapper import *


#-------------------------------------------------------------------------
# CalleeIfcRTL
#-------------------------------------------------------------------------
class CalleeIfcRTL( Interface ):

  def construct( s, ArgType, RetType ):

    s.arg = InPort( ArgType ) if ArgType else None
    s.ret = OutPort( RetType ) if RetType else None
    s.en = InPort( Bits1 )
    s.rdy = OutPort( Bits1 )

  def connect( s, other, parent ):
    if isinstance( other, CalleeIfcRTL ):
      return Interface.connect( s, other, parent )
    else:
      if other.is_interface():

        try:
          args = other.method_spec.args
          rets = other.method_spec.rets
        except:
          args, rets = inspect_rtl( other )

        if args:
          arg_names = [ arg_name for arg_name, _ in s.arg._dsl.Type.fields ]
          assert set( arg_names ) == set( args.keys() )
          for arg_name in arg_names:
            parent.connect_pairs(
                getattr( s.arg, arg_name ), getattr( other, arg_name ) )
        else:
          assert s.arg is None

        if rets:
          ret_names = [ ret_name for ret_name, _ in s.ret._dsl.Type.fields ]
          assert set( ret_names ) == set( rets.keys() )
          for ret_name in ret_names:
            parent.connect_pairs(
                getattr( s.ret, ret_name ), getattr( other, ret_name ) )
        else:
          assert s.ret is None

        parent.connect_pairs( s.rdy, other.rdy, s.en, other.en )

        return True

    return False


#-------------------------------------------------------------------------
# mk_ifc_from_spec
#-------------------------------------------------------------------------
def mk_ifc_from_spec( spec ):
  name = spec.method_name
  arg_type = mk_bit_struct( name + "_Arg",
                            spec.args.items() ) if spec.args else None
  ret_type = mk_bit_struct( name + "_Ret",
                            spec.rets.items() ) if spec.rets else None
  return CalleeIfcRTL( arg_type, ret_type )


#-------------------------------------------------------------------------
# RTL2CL
#-------------------------------------------------------------------------
class RTL2CL( Component ):

  def construct( s, spec ):

    ifc = mk_ifc_from_spec( spec )
    s.ifc_rtl = ifc.inverse()

    s.called = False
    s.rdy = False

    if spec.args:
      s.arg = s.ifc_rtl.arg._dsl.Type()

      @s.update
      def update_en_args():
        s.ifc_rtl.en = Bits1( 1 ) if s.called else Bits1( 0 )
        s.ifc_rtl.arg = s.arg
        s.called = False

    else:
      s.arg = None

      @s.update
      def update_en_args():
        s.ifc_rtl.en = Bits1( 1 ) if s.called else Bits1( 0 )
        s.called = False

    if spec.rets:
      s.ret = s.ifc_rtl.ret._dsl.Type()

      @s.update
      def update_ret():
        s.ret = s.ifc_rtl.ret

      s.add_constraints( U( update_ret ) < M( s.cl_method ) )
    else:
      s.ret = None

    @s.update
    def update_rdy():
      s.rdy = True if s.ifc_rtl.rdy else False

    s.add_constraints(
        U( update_rdy ) < M( s.cl_method ),
        M( s.cl_method ) < U( update_en_args ) )

  @non_blocking( lambda s: s.rdy )
  def cl_method( s, **kwargs ):
    if s.arg:
      for k, v in kwargs.items():
        s.arg.__dict__[ k ] = v
    s.called = True
    return s.ret


#-------------------------------------------------------------------------
# ExampleWrapper
#-------------------------------------------------------------------------
class ExampleWrapper( Component ):
  model_name = "ref"

  def construct( s, model ):
    s.model = model
    s.method_specs = inspect_rtl( s.model )

    s.enq_adapter = RTL2CL( s.method_specs[ "enq" ] )
    s.deq_adapter = RTL2CL( s.method_specs[ "deq" ] )
    s.connect( s.model.enq, s.enq_adapter.ifc_rtl )
    s.connect( s.model.deq, s.deq_adapter.ifc_rtl )

    s.deq = NonBlockingCalleeIfc()
    s.enq = NonBlockingCalleeIfc()
    s.connect( s.deq, s.deq_adapter.cl_method )
    s.connect( s.enq, s.enq_adapter.cl_method )

  def line_trace( s ):
    return s.model.line_trace()


#-------------------------------------------------------------------------
# QueueMachine
#-------------------------------------------------------------------------
class QueueMachine( RuleBasedStateMachine ):

  def __init__( s ):
    super( QueueMachine, s ).__init__()
    s.dut = ExampleWrapper( SingleEntryBypassQueue( Bits16 ) )
    s.ref = BypassQueueCL( 1 )

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

  def deq_rdy( s ):
    dut_rdy = s.dut.deq.rdy()
    ref_rdy = s.ref.deq.rdy()
    assert dut_rdy == ref_rdy
    return dut_rdy

  @precondition( lambda s: s.deq_rdy() )
  @rule()
  def deq( s ):
    assert s.dut.deq().msg == s.ref.deq()

  def enq_rdy( s ):
    dut_rdy = s.dut.enq.rdy()
    ref_rdy = s.ref.enq.rdy()
    assert dut_rdy == ref_rdy
    return dut_rdy

  @precondition( lambda s: s.enq_rdy() )
  @rule( msg=st.integers( min_value=0, max_value=15 ) )
  def enq( s, msg ):
    s.dut.enq( msg=msg )
    s.ref.enq( msg=msg )


#-------------------------------------------------------------------------
# test_stateful
#-------------------------------------------------------------------------
def test_stateful():
  run_state_machine_as_test( QueueMachine )
