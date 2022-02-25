"""
========================================================================
ValRdyIfc
========================================================================
RTL val/rdy interface.

Author : Shunning Jiang
  Date : Apr 5, 2019
"""
from pymtl3 import *
from pymtl3.extra import clone_deepcopy
from pymtl3.dsl.errors import InvalidConnectionError

#-------------------------------------------------------------------------
# valrdy_to_str
#-------------------------------------------------------------------------

def valrdy_to_str( msg, val, rdy, trace_len=15 ):
  if     val and not rdy: return "#".ljust( trace_len )
  if not val and     rdy: return " ".ljust( trace_len )
  if not val and not rdy: return ".".ljust( trace_len )
  return f"{msg}".ljust( trace_len ) # val and rdy

#-------------------------------------------------------------------------
# RecvIfcRTL
#-------------------------------------------------------------------------

class RecvIfcRTL( Interface ):

  def construct( s, Type ):

    s.msg = InPort( Type )
    s.val = InPort()
    s.rdy = OutPort()

    s.MsgType   = Type
    s.trace_len = len(str(Type()))

  def connect( s, other, parent ):

    # SendCL (other) -> [ RecvCL -> SendRTL ] -> RecvRTL
    if isinstance( other, CallerIfcCL ):
      connect_valid = True
      # Create an adapter and add to parents
      m = RecvCL2SendRTL( s.MsgType )

      if hasattr( parent, "RecvCL2SendRTL_count" ):
        count = parent.RecvRTL2SendCL_count
        setattr( parent, f"RecvCL2SendRTL_{count}", m )
      else:
        parent.RecvCL2SendRTL_count = 0
        parent.RecvCL2SendRTL_0     = m

      other  //= m.recv
      m.send //= s
      parent.RecvCL2SendRTL_count += 1
      return True

    # RecvRTL -> [ RecvRTL -> SendCL ] -> RecvCL (other)
    elif isinstance( other, CalleeIfcCL ):
      if s._dsl.level <= other._dsl.level:
        raise InvalidConnectionError(
            "CL2RTL connection is not supported between RecvIfcRTL"
            " and CalleeIfcCL.\n"
            f"          - level {s._dsl.level    }: {s:r    } (class {type(s)    })\n"
            f"          - level {other._dsl.level}: {other:r} (class {type(other)})"
        )
      else:
        # Create an adapter and add to parents
        m = RecvRTL2SendCL( s.MsgType )

        if hasattr( parent, "RecvRTL2SendCL_count" ):
          count = parent.RecvRTL2SendCL_count
          setattr( parent, f"RecvRTL2SendCL_{count}", m )
        else:
          parent.RecvRTL2SendCL_count = 0
          parent.RecvRTL2SendCL_0     = m

        s      //= m.recv
        m.send //= other
        parent.RecvRTL2SendCL_count += 1
        return True

    return False

  def __str__( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy, s.trace_len )

#-------------------------------------------------------------------------
# SendIfcRTL
#-------------------------------------------------------------------------

class SendIfcRTL( Interface ):

  def construct( s, Type ):

    s.msg = OutPort( Type )
    s.val = OutPort()
    s.rdy = InPort()

    s.trace_len = len(str(Type()))

  def connect( s, other, parent ):
    # SendRTL -> [ RecvRTL -> SendCL ] -> RecvCL (other)
    if isinstance( other, CalleeIfcCL ):
      # Create an adapter and add to parents
      m = RecvRTL2SendCL( s.MsgType )

      if hasattr( parent, "RecvRTL2SendCL_count" ):
        count = parent.RecvCL2SendRTL_count
        setattr( parent, f"RecvRTL2SendCL_{count}", m )
      else:
        parent.RecvRTL2SendCL_count = 0
        parent.RecvRTL2SendCL_0     = m

      s      //= m.recv
      m.send //= other
      parent.RecvRTL2SendCL_count += 1
      return True

    # SendCL (other) -> [ RecvCL -> SendRTL ] -> SendRTL
    elif isinstance( other, CallerIfcCL ):
      if s._dsl.level <= other._dsl.level:
        raise InvalidConnectionError(
            "CL2RTL connection is not supported between RecvIfcRTL"
            " and CalleeIfcCL.\n"
            f"          - level {s._dsl.level    }: {s:r    } (class {type(s)    })\n"
            f"          - level {other._dsl.level}: {other:r} (class {type(other)})"
        )
      else:
        # Create an adapter and add to parents
        m = RecvCL2SendRTL( s.MsgType )

        if hasattr( parent, "RecvCL2SendRTL_count" ):
          count = parent.RecvCL2SendRTL_count
          setattr( parent, f"RecvCL2SendRTL_{count}", m )
        else:
          parent.RecvCL2SendRTL_count = 0
          parent.RecvCL2SendRTL_0     = m

        other  //= m.recv
        m.send //= s
        parent.RecvCL2SendRTL_count += 1
        return True

    return False

  def __str__( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy, s.trace_len )

#-------------------------------------------------------------------------
# MasterIfcRTL
#-------------------------------------------------------------------------

class MasterIfcRTL( Interface ):
  def construct( s, ReqType, RespType ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.req  = SendIfcRTL( Type=ReqType )
    s.resp = RecvIfcRTL( Type=RespType )
  def __str__( s ):
    return f"{s.req}|{s.resp}"

class MinionIfcRTL( Interface ):
  def construct( s, ReqType, RespType ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.req  = RecvIfcRTL( Type=ReqType )
    s.resp = SendIfcRTL( Type=RespType )
  def __str__( s ):
    return f"{s.req}|{s.resp}"

#=========================================================================
# Interface adapters
#=========================================================================

#-------------------------------------------------------------------------
# RecvCL2SendRTL
#-------------------------------------------------------------------------

class RecvCL2SendRTL( Component ):

  def construct( s, MsgType ):

    # Interface
    s.send = SendIfcRTL( MsgType )

    # Declarations
    s.entry = None

    @update_once
    def up_clear():
      if s.send.val & s.send.rdy:
        s.entry = None

    @update
    def up_send_rtl():
      if s.entry is None:
        s.send.val @= 0
      else:
        s.send.val @= 1
        s.send.msg @= s.entry

    # Bypass behavior
    # Recv message -- Update valid -- Clear entry when rdy is settled
    # This should work if rdy depends on val
    s.add_constraints(
      U( up_send_rtl ) < U( up_clear    ),
      M( s.recv      ) < U( up_send_rtl ),
      M( s.recv.rdy  ) < U( up_send_rtl ),
    )

  @non_blocking( lambda s: s.entry is None )
  def recv( s, msg ):
    s.entry = clone_deepcopy( msg )

  def line_trace( s ):
    return f"{s.recv}({'*' if s.entry is not None else' '}){s.send}"

#-------------------------------------------------------------------------
# RecvRTL2SendCL
#-------------------------------------------------------------------------

class RecvRTL2SendCL( Component ):

  def construct( s, MsgType ):

    # Interface
    s.recv = RecvIfcRTL ( MsgType )
    s.send = CallerIfcCL( MsgType )

    # Declarations
    s.send_rdy = False

    @update_once
    def up_recv_rtl_rdy():
      s.send_rdy = s.send.rdy() & ~s.reset
      s.recv.rdy @= s.send_rdy

    @update
    def up_send_cl():
      if s.send_rdy and s.recv.val:
        s.send( s.recv.msg )

    # Bypass behavior
    # Update rdy --> Call send if valid
    # This should work for any val/rdy dependencies
    s.add_constraints( U( up_recv_rtl_rdy ) < U( up_send_cl ) )

  def line_trace( s ):
    return f"{s.recv}(){s.send}"

