#=========================================================================
# generic_method_ifcs.py
#=========================================================================
# RTL method interface. RTL equivalence of NonBlockingCalleeIfc in CL
#
# Author : Yixiao Zhang
#   Date : June 10, 2019

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

      s.cl_method = NonBlockingCalleeIfc(
          method=s.cl_callee_method, rdy=lambda: s.rdy )

      # add constraints between callee method and upblk
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
