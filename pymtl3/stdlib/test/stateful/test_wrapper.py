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

    s.rtl_caller = CallerIfcRTL( MsgType=MsgType, RetType=RetType )

    s.MsgType = MsgType
    s.RetType = RetType

    s.rdy = False
    s.called = False

    # generate upblk depending on args

    if MsgType:
      s.msg = ArgType()

      # update args & en
      @s.update
      def up_en_args():
        s.rtl_caller.en  = Bits1( s.called )
        s.rtl_caller.msg = s.msg

      s.cl_callee = CalleeIfcCL( method=s.cl_callee_method, rdy=lambda: s.rdy )

      # add constraints between callee method and upblk to model combinational behavior
      s.add_constraints( M( s.cl_method ) < U( up_en_args ) )

    else:
      # no args, update en
      @s.update
      def up_en():
        s.ifc_rtl_caller.en = Bits1( 1 ) if s.called else Bits1( 0 )

      s.cl_method = NonBlockingCalleeIfc(
          method=s.cl_callee_method_no_arg, rdy=lambda: s.rdy )

      # add constraints between callee method and upblk
      s.add_constraints( M( s.cl_method ) < U( up_en ) )

    # generate upblk depending on rets
    if RetType:
      # create tmp var for rets
      s.rets = RetType()

      # generate upblk for rets
      @s.update
      def up_rets():
        s.rets = s.ifc_rtl_caller.rets

      s.add_constraints( U( up_rets ) < M( s.cl_method ) )

    else:
      # return None if no ret
      s.rets = None

    # Generate upblk and add constraints for rdy
    @s.update
    def up_rdy():
      s.rdy = bool(s.rtl_caller.rdy)

    s.add_constraints( U( up_rdy ) < M( s.cl_method ) )

  def cl_callee_method( s, msg ):
    s.args = s.ArgType()
    s.args.__dict__.update( kwargs )
    s.called = True
    return s.rets

  def cl_callee_method_no_arg( s ):
    s.called = True
    return s.rets

#-------------------------------------------------------------------------
# RTL2CLWrapper
#-------------------------------------------------------------------------
class RTL2CLWrapper( Component ):

  def __init__( s, rtl_model ):
    super( RTL2CLWrapper, s ).__init__()

    s.model_name = type( rtl_model ).__name__

  def construct( s, rtl_model ):
    """Create adapter & add top-level method for each ifc in rtl_model
    """

    s.model = rtl_model

    for name, obj in rtl_model.__dict__.items():
      if isinstance( obj, CalleeIfcRTL ):
        added_ifc = CalleeIfcCL()
        setattr( s, name, added_ifc )
        print(added_ifc.__dict__)
        connect( added_ifc, obj )

  def line_trace( s ):
    return s.model.line_trace()
