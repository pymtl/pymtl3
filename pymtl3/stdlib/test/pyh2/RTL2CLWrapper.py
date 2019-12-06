"""
==========================================================================
RTL2CLWrapper
==========================================================================
Generic wrapper that wraps RTL model into CL.

Author : Yanghui Ou, Yixiao Zhang, Shunning Jiang
  Date : Dec 2, 2019
"""
from pymtl3 import *

"""
notes:
  Basically we hit the same circumstance when CL source sends a message to
  an RTL design that has rdy depend on enable which is technically not
  correct but for imported verilog design it is the case.
"""


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

    keys = sorted( rtl_model.__dict__.keys() )
    for name in keys:
      obj = rtl_model.__dict__[ name ]
      if isinstance( obj, CalleeIfcRTL ):
        assert obj.MsgType is None or obj.RetType is None, \
          f"Currently we cannot wrap callee interfaces with both arguments and return values like '{obj}' of class '{obj.__class__}'."
        added_ifc     = CalleeIfcCL()
        added_adapter = CalleeRTL2CL( obj.MsgType, obj.RetType )
        setattr( s, name, added_ifc )
        setattr( s, name+"_adapter", added_adapter )

        connect( added_ifc, added_adapter.cl_callee )
        connect( added_adapter.rtl_caller, obj )

        s.method_specs[ name ] = (obj.MsgType, obj.RetType)

  def line_trace( s ):
    return s.model.line_trace()

#-------------------------------------------------------------------------
# CalleeRTL2CL
#-------------------------------------------------------------------------
class CalleeRTL2CL( Component ):

  def construct( s, MsgType, RetType ):
    s.MsgType = MsgType
    s.RetType = RetType

    # These variable are set by the method
    s.rdy    = False
    s.called = False

    s.rtl_caller = CallerIfcRTL( en=True, rdy=True, MsgType=MsgType, RetType=RetType )

    if MsgType is None:
      if RetType is None: cl_callee = s.cl_callee_method_no_arg_no_ret
      else:               cl_callee = s.cl_callee_method_no_arg_yes_ret
    else:
      if RetType is None: cl_callee = s.cl_callee_method_yes_arg_no_ret
      else:               cl_callee = s.cl_callee_method_yes_arg_yes_ret

    s.cl_callee  = CalleeIfcCL( method=cl_callee, rdy=lambda: s.rdy )

    # This adapter always has ready and called block
    # Set rdy before any rdy call
    @s.update
    def up_rdy():
      s.rdy = bool(s.rtl_caller.rdy)

    s.add_constraints( U( up_rdy ) < M( s.cl_callee.rdy ) )

    # We clear called flag before any method call
    @s.update
    def up_called():
      s.called = False

    s.add_constraints( U( up_called ) < M( s.cl_callee ) )

    # Add upblk depending on args (msg)

    if MsgType:
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
        s.rtl_caller.en = Bits1( s.called )

      # add constraints between callee method and upblk
      s.add_constraints( M( s.cl_callee ) < U( up_en ) )

    # Add upblk depending on ret
    if RetType:
      s.ret = RetType()

      @s.update
      def up_ret():
        s.ret = s.rtl_caller.ret

      s.add_constraints( U( up_ret ) < M( s.cl_callee ) )

  def cl_callee_method_yes_arg_yes_ret( s, msg ):
    assert isinstance( msg, s.MsgType )
    s.called = True
    s.msg = msg
    return s.ret

  def cl_callee_method_yes_arg_no_ret( s, msg ):
    assert isinstance( msg, s.MsgType )
    s.called = True
    s.msg = msg

  def cl_callee_method_no_arg_yes_ret( s ):
    s.called = True
    return s.ret

  def cl_callee_method_no_arg_no_ret( s ):
    s.called = True
