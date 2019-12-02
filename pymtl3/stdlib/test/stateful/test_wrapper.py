#=========================================================================
# test_wrapper
#=========================================================================
# Wrappers for testing rtl model.
#
# Author : Yixiao Zhang
#   Date : June 10, 2019

import inspect

import attr
import hypothesis.strategies as st

from pymtl3 import *
from pymtl3.dsl.ComponentLevel6 import ComponentLevel6


#-------------------------------------------------------------------------
# list_string
#-------------------------------------------------------------------------
def list_string( lst ):
  return ", ".join([ str( x ) for x in lst ] )

#-------------------------------------------------------------------------
# Method
#-------------------------------------------------------------------------
@attr.s()
class Method( object ):
  method_name = attr.ib()
  args = attr.ib( default={} )
  rets_type = attr.ib( default={} )

#-------------------------------------------------------------------------
# rename
#-------------------------------------------------------------------------
def rename( name ):
  def wrap( f ):
    f.__name__ = name
    return f
  return wrap

def kwarg_to_str( kwargs ):
  return list_string(
      [ "{k}={v}".format( k=k, v=v ) for k, v in kwargs.items() ] )

#-------------------------------------------------------------------------
# CalleeRTL2CL
#-------------------------------------------------------------------------
class CalleeRTL2CL( Component ):

  def construct( s, MsgType, RetType ):

    s.rtl_caller = CallerIfcRTL( en=True, rdy=True, MsgType=MsgType, RetType=RetType )

    s.MsgType = MsgType
    s.RetType = RetType

    s.rdy = False
    s.called = False

    # generate upblk depending on args (msg)
    if MsgType:
      s.cl_callee = CalleeIfcCL( method=s.cl_callee_method, rdy=lambda: s.rdy )

      s.msg = MsgType()

      @s.update
      def up_en_args():
        s.rtl_caller.en  = Bits1( s.called )
        s.rtl_caller.msg = s.msg


      # add constraints between callee method and upblk to model combinational behavior
      s.add_constraints( M( s.cl_callee ) < U( up_en_args ) )

    else:
      # no args, update en
      @s.update
      def up_en():
        s.rtl_caller.en = Bits1( 1 ) if s.called else Bits1( 0 )

      s.cl_callee = CalleeIfcCL( method=s.cl_callee_method_no_arg, rdy=lambda: s.rdy )

      # add constraints between callee method and upblk
      s.add_constraints( M( s.cl_callee ) < U( up_en ) )

    # generate upblk depending on rets
    if RetType:
      s.ret = RetType()

      @s.update
      def up_ret():
        s.ret = s.rtl_caller.ret

      s.add_constraints( U( up_ret ) < M( s.cl_callee ) )

    else:
      # return None if no ret
      s.rets = None

    # Generate upblk and add constraints for rdy
    @s.update
    def up_rdy():
      s.rdy = bool(s.rtl_caller.rdy)

    s.add_constraints( U( up_rdy ) < M( s.cl_callee ) )

  def cl_callee_method( s, msg ):
    assert isinstance( msg, s.MsgType )
    s.msg = msg
    return s.ret

  def cl_callee_method_no_arg( s ):
    s.called = True
    return s.ret

#-------------------------------------------------------------------------
# RTL2CLWrapper
#-------------------------------------------------------------------------
class RTL2CLWrapper( Component ):

  def __init__( s, rtl_model ):
    super( RTL2CLWrapper, s ).__init__()

    s.model_name = type( rtl_model ).__name__

  def construct( s, rtl_model ):

    s.model = rtl_model
    s.method_specs = {}

    for name, obj in rtl_model.__dict__.items():
      if isinstance( obj, CalleeIfcRTL ):
        added_ifc     = CalleeIfcCL()
        added_adapter = CalleeRTL2CL( obj.MsgType, obj.RetType )
        setattr( s, name, added_ifc )
        setattr( s, name+"_adapter", added_adapter )

        connect( added_ifc, added_adapter.cl_callee )
        connect( added_adapter.rtl_caller, obj )

        s.method_specs[ name ] = (obj.MsgType, obj.RetType)

  def line_trace( s ):
    return s.model.line_trace()
