#=========================================================================
# generic_method_ifcs.py
#=========================================================================
# RTL method interface. RTL equivalence of NonBlockingCalleeIfc in CL
#
# Author : Yixiao Zhang
#   Date : June 10, 2019

from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.dsl.errors import InvalidConnectionError


#-------------------------------------------------------------------------
# CalleeRTL2CL
#-------------------------------------------------------------------------
class CalleeRTL2CL( Component ):

  def construct( s, ArgType, RetType ):

    s.ifc_rtl_caller = CallerIfcRTL( ArgType, RetType )

    s.ArgType = ArgType
    s.RetType = RetType

    s.rdy = False
    s.called = False

    # clear call signal
    @s.update_on_edge
    def up_clear():
      s.called = False

    # generate upblk depending on args

    if ArgType:
      s.args = ArgType()

      # update args & en
      @s.update
      def up_en_args():
        s.ifc_rtl_caller.en = Bits1( 1 ) if s.called else Bits1( 0 )
        s.ifc_rtl_caller.args = s.args

      # select which method to use for NonBlockingCalleeIfc
      s.cl_method = s.cl_callee_method

      # add constraints between callee method and upblk
      s.add_constraints( M( s.cl_method ) < U( up_en_args ) )

    else:
      # no args, update en
      @s.update
      def up_en():
        s.ifc_rtl_caller.en = Bits1( 1 ) if s.called else Bits1( 0 )

      # select which method to use for NonBlockingCalleeIfc
      s.cl_method = s.cl_callee_method_no_arg

      # add constraints between callee method and upblk
      s.add_constraints( M( s.cl_method ) < U( up_en ) )

    s.cl_method = NonBlockingCalleeIfc( method=s.cl_method, rdy=lambda: s.rdy )

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
      s.rdy = True if s.ifc_rtl_caller.rdy else False

    s.add_constraints( U( up_rdy ) < M( s.cl_method ) )

  def cl_callee_method( s, **kwargs ):
    s.args = s.ArgType()
    s.args.__dict__.update( kwargs )
    s.called = True
    return s.rets

  def cl_callee_method_no_arg( s ):
    s.called = True
    return s.rets


#-------------------------------------------------------------------------
# CallerIfcRTL
#-------------------------------------------------------------------------
class CallerIfcRTL( Interface ):

  def construct( s, ArgType=None, RetType=None ):

    s.ArgType = ArgType
    s.RetType = RetType

    if ArgType:
      s.args = OutPort( ArgType )
    else:
      s.args = None

    if RetType:
      s.rets = InPort( RetType )
    else:
      s.rets = None

    s.en = OutPort( Bits1 )
    s.rdy = InPort( Bits1 )


#-------------------------------------------------------------------------
# CalleeIfcRTL
#-------------------------------------------------------------------------
class CalleeIfcRTL( Interface ):

  def construct( s, ArgType=None, RetType=None ):

    s.ArgType = ArgType
    s.RetType = RetType

    if ArgType:
      s.args = InPort( ArgType )
    else:
      s.args = None

    if RetType:
      s.rets = OutPort( RetType )
    else:
      s.rets = None

    s.en = InPort( Bits1 )
    s.rdy = OutPort( Bits1 )

  def connect( s, other, parent ):
    if isinstance( other, NonBlockingCalleeIfc ):
      if s._dsl.level <= other._dsl.level:
        raise InvalidConnectionError(
            "CL2RTL connection is not supported between CalleeIfcRTL"
            " and NonBlockingCalleeIfc.\n"
            "          - level {}: {} (class {})\n"
            "          - level {}: {} (class {})".format(
                s._dsl.level, repr( s ), type( s ), other._dsl.level,
                repr( other ), type( other ) ) )

      rtl2cl_adapter = CalleeRTL2CL( s.ArgType, s.RetType )

      setattr( parent, "callee_rtl2cl_adapter_" + s._dsl.my_name,
               rtl2cl_adapter )

      parent.connect_pairs( s, rtl2cl_adapter.ifc_rtl_caller, other,
                            rtl2cl_adapter.cl_method )

      return True
    return False


#-------------------------------------------------------------------------
# mk_callee_ifc_args_rets
#-------------------------------------------------------------------------
def mk_callee_ifc_args_rets( fields ):
  if fields:
    # mangle arg bit_struct name by fields
    cls_name = "CalleeIfcRTL"
    for name, field_type in fields:
      cls_name += "_{}_{}".format( name, field_type.__name__ )

    return mk_bit_struct( cls_name, fields )

  else:
    return None


#-------------------------------------------------------------------------
# callee_ifc_rtl
#-------------------------------------------------------------------------
def callee_ifc_rtl( ArgTypes=None, RetTypes=None ):
  return CalleeIfcRTL(
      mk_callee_ifc_args_rets( ArgTypes ), mk_callee_ifc_args_rets( RetTypes ) )


#-------------------------------------------------------------------------
# caller_ifc_rtl
#-------------------------------------------------------------------------
def caller_ifc_rtl( ArgTypes=None, RetTypes=None ):
  return CallerIfcRTL(
      mk_callee_ifc_args_rets( ArgTypes ), mk_callee_ifc_args_rets( RetTypes ) )
