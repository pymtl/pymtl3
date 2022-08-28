from pymtl3 import *
from pymtl3.extra import clone_deepcopy
from pymtl3.stdlib.connects import connect_pairs

def enrdy_to_str( msg, en, rdy, trace_len=15 ):
  if     en and not rdy: return "X".ljust( trace_len ) # Not allowed!
  if not en and     rdy: return " ".ljust( trace_len ) # Idle
  if not en and not rdy: return "#".ljust( trace_len ) # Stalled
  return f"{msg}".ljust( trace_len ) # en and rdy

class RecvIfc( Interface ):

  def construct( s, Type ):
    s.en = InPort()
    s.rdy = OutPort()
    s.msg = InPort( Type )

    s.MsgType = Type

    s.trace_len = len(str(Type()))

  def connect( s, other, parent ):
    # We are doing SendCL (other) -> [ RecvCL -> SendRTL ] -> RecvRTL (s)
    # SendCL is a caller interface
    if isinstance( other, CallerIfcCL ):
      m = RecvCL2SendRTL( s.MsgType )

      if hasattr( parent, "RecvCL2SendRTL_count" ):
        count = parent.RecvCL2SendRTL_count
        setattr( parent, "RecvCL2SendRTL_" + str( count ), m )
      else:
        parent.RecvCL2SendRTL_count = 0
        parent.RecvCL2SendRTL_0 = m

      connect_pairs(
        other,  m.recv,
        m.send.msg, s.msg,
        m.send.en,  s.en,
        m.send.rdy, s.rdy
      )
      parent.RecvCL2SendRTL_count += 1
      return True

    elif isinstance( other, CalleeIfcCL ):
      if s._dsl.level <= other._dsl.level:
        raise InvalidConnectionError(
            "CL2RTL connection is not supported between RecvIfcRTL"
            " and CalleeIfcCL.\n"
            "          - level {}: {} (class {})\n"
            "          - level {}: {} (class {})".format(
                s._dsl.level, repr( s ), type( s ), other._dsl.level,
                repr( other ), type( other ) ) )

      m = RecvCL2SendRTL( s.MsgType )

      if hasattr( parent, "RecvCL2SendRTL_count" ):
        count = parent.RecvCL2SendRTL_count
        setattr( parent, "RecvCL2SendRTL_" + str( count ), m )
      else:
        parent.RecvCL2SendRTL_count = 0
        parent.RecvCL2SendRTL_0 = m

      connect_pairs(
        other,  m.recv,
        m.send.msg, s.msg,
        m.send.en,  s.en,
        m.send.rdy, s.rdy
      )
      parent.RecvCL2SendRTL_count += 1
      return True

    return False

  def __str__( s ):
    return enrdy_to_str( s.msg, s.en, s.rdy, s.trace_len )

class SendIfc( Interface ):

  def construct( s, Type ):
    s.en = OutPort()
    s.rdy = InPort()
    s.msg = OutPort( Type )

    s.MsgType = Type

    s.trace_len = len(str(Type()))

  def connect( s, other, parent ):
    # We are doing SendRTL (s) -> [ RecvRTL -> SendCL ] -> RecvCL (other)
    # RecvCL is a callee interface
    if isinstance( other, CalleeIfcCL ):
      m = RecvRTL2SendCL( s.MsgType )

      if hasattr( parent, "RecvRTL2SendCL_count" ):
        count = parent.RecvRTL2SendCL_count
        setattr( parent, "RecvRTL2SendCL_" + str( count ), m )
      else:
        parent.RecvRTL2SendCL_count = 0
        parent.RecvRTL2SendCL_0 = m

      connect_pairs(
        m.send, other,
        s.msg, m.recv.msg,
        s.en,  m.recv.en,
        s.rdy, m.recv.rdy,
      )
      parent.RecvRTL2SendCL_count += 1
      return True

    return False

  def __str__( s ):
    return enrdy_to_str( s.msg, s.en, s.rdy, s.trace_len )

class GetIfc( Interface ):

  def construct( s, Type ):
    s.en = OutPort()
    s.rdy = InPort()
    s.msg = InPort( Type )

    s.trace_len = len(str(Type()))

  def __str__( s ):
    return enrdy_to_str( s.msg, s.en, s.rdy, s.trace_len )

# Helper component to connect a GiveIfc to a RecvIfc
class And( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( Type )

    @update
    def up_and():
      s.out @= s.in0 & s.in1

class GiveIfc( Interface ):

  def construct( s, Type ):
    s.en = InPort()
    s.rdy = OutPort()
    s.msg = OutPort( Type )

    s.trace_len = len(str(Type()))

  def connect( s, other, parent ):
    # We are doing GiveIfc (s) -> [ AND ] -> RecvIfc (other)
    # Basically we AND the rdy of both sides for enable
    if isinstance( other, RecvIfc ):
      connect( s.msg, other.msg )

      m = And( Bits1 )

      if hasattr( parent, "give_recv_ander_cnt" ):
        cnt = parent.give_recv_ander_cnt
        setattr( parent, "give_recv_ander_" + str( cnt ), m )
      else:
        parent.give_recv_ander_cnt = 0
        parent.give_recv_ander_0   = m

      connect_pairs(
        m.in0, s.rdy,
        m.in1, other.rdy,
        m.out, s.en,
        m.out, other.en,
      )
      parent.give_recv_ander_cnt += 1
      return True
    return False

  def __str__( s ):
    return enrdy_to_str( s.msg, s.en, s.rdy, s.trace_len )

class EnqIfc( RecvIfc ):

  def construct( s, Type ):
    super().construct( Type )

class DeqIfc( GiveIfc ):

  def construct( s, Type ):
    super().construct( Type )

#-------------------------------------------------------------------------
# RecvCL2SendRTL
#-------------------------------------------------------------------------

class RecvCL2SendRTL( Component ):

  def construct( s, MsgType ):

    # Interface

    s.send = SendIfc( MsgType )

    s.entry = None

    @update_once
    def up_clear():
      if s.send.en: # constraints reverse this
        s.entry = None

    @update
    def up_send_rtl():
      if s.entry is None:
        s.send.en  @= b1( 0 )
      else:
        s.send.en  @= b1( s.send.rdy )
        s.send.msg @= s.entry

    s.add_constraints(
      U( up_clear )   < WR( s.send.en ),
      U( up_clear )   < M( s.recv ),
      U( up_clear )   < M( s.recv.rdy ),
      M( s.recv )     < U( up_send_rtl ),
      M( s.recv.rdy ) < U( up_send_rtl )
    )

  @non_blocking( lambda s : s.entry is None )
  def recv( s, msg ):
    s.entry = clone_deepcopy( msg )

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.send )

#-------------------------------------------------------------------------
# RecvRTL2SendCL
#-------------------------------------------------------------------------

class RecvRTL2SendCL( Component ):

  def construct( s, MsgType ):

    # Interface

    s.recv = RecvIfc( MsgType )
    s.send = CallerIfcCL()

    s.sent_msg = None
    s.send_rdy = False

    @update_once
    def up_recv_rtl_rdy():
      s.send_rdy = s.send.rdy() & ~s.reset
      s.recv.rdy @= s.send_rdy

    @update_once
    def up_send_cl():
      s.sent_msg = None
      if s.recv.en:
        s.send( s.recv.msg )
        s.sent_msg = s.recv.msg

    s.add_constraints( U( up_recv_rtl_rdy ) < U( up_send_cl ) )

  def line_trace( s ):
    return "{}(){}".format(
      s.recv.line_trace(),
      enrdy_to_str( s.sent_msg, s.sent_msg is not None, s.send_rdy )
    )
