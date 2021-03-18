import greenlet
from pymtl3 import *
from pymtl3.extra import clone_deepcopy
from pymtl3.stdlib.mem.MemMsg import MemMsgType
from .ifcs import RecvIfcRTL, SendIfcRTL, MasterIfcRTL

class RecvQueueAdapter( Component ):

  @blocking
  def deq( s ):
    while s.entry is None:
      greenlet.getcurrent().parent.switch(0)
    ret = s.entry
    s.entry = None
    return ret

  def construct( s, Type ):
    s.recv = RecvIfcRTL( Type )
    s.entry = None

    @update_once
    def up_recv_rdy():
      s.recv.rdy @= (s.entry is None)

    @update_once
    def up_recv_msg():
      if (s.entry is None) & s.recv.val:
        s.entry = clone_deepcopy( s.recv.msg )

    s.add_constraints( M( s.deq )       < U( up_recv_rdy ), # deq before recv in a cycle -- pipe behavior
                       U( up_recv_rdy ) < U( up_recv_msg ) )

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.send )

class SendQueueAdapter( Component ):

  @blocking
  def enq( s, msg ):
    while s.entry is not None:
      greenlet.getcurrent().parent.switch(0)

    s.entry = clone_deepcopy(msg)

  def construct( s, Type ):
    s.send = SendIfcRTL( Type )
    s.entry = None

    s.sent = Wire()

    @update
    def up_send():
      if s.entry is None:
        s.send.val @= 0
      else:
        s.send.val @= 1
        s.send.msg @= s.entry

    @update_ff
    def up_sent():
      s.sent <<= s.send.val & s.send.rdy

    @update_once
    def up_clear():
      if s.sent: # constraints reverse this
        s.entry = None

    s.add_constraints( U( up_clear ) < M( s.enq ),
                       M( s.enq )    < U( up_send ) )

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.send )

class MemMasterAdapter( Component ):

  @blocking
  def read( s, addr, nbytes ):
    while s.req_entry is not None:
      greenlet.getcurrent().parent.switch(0)

    s.req_entry = s.create_req( MemMsgType.READ, 0, addr, nbytes )

    while s.resp_entry is None:
      greenlet.getcurrent().parent.switch(0)

    ret = s.resp_entry.data[0:nbytes<<3]
    s.resp_entry = None
    return ret

  @blocking
  def write( s, addr, nbytes, data ):
    while s.req_entry is not None:
      greenlet.getcurrent().parent.switch(0)

    s.req_entry = s.create_req( MemMsgType.WRITE, 0, addr, nbytes, data )

    while s.resp_entry is None:
      greenlet.getcurrent().parent.switch(0)

    s.resp_entry = None

  @blocking
  def amo( s, amo_type, addr, nbytes, data ):
    while s.req_entry is not None:
      greenlet.getcurrent().parent.switch(0)

    s.req_entry = s.create_req( amo_type, 0, addr, nbytes, data )

    while s.resp_entry is None:
      greenlet.getcurrent().parent.switch(0)

    ret = s.resp_entry.data[0:nbytes<<3]
    s.resp_entry = None
    return ret

  def construct( s, ReqType, RespType ):
    s.master = MasterIfcRTL( ReqType, RespType )

    # Use create_req to handle type mismatch
    Tlen  = ReqType.get_field_type('len')
    Tdata = ReqType.get_field_type('data')
    s.create_req = lambda a,b,c,d,e=0: ReqType( a, b, c, Tlen(d, trunc_int=True), Tdata(int(e)) )

    s.req_entry  = None
    s.resp_entry = None

    # req path

    s.req_sent = Wire()

    @update_ff
    def up_req_sent():
      s.req_sent <<= s.master.req.val & s.master.req.rdy

    @update
    def up_clear_req():
      if s.req_sent:
        s.req_entry = None

    @update_once
    def up_send_req():
      if s.req_entry is None:
        s.master.req.val @= 0
      else:
        s.master.req.val @= 1
        s.master.req.msg @= s.req_entry

    # resp path
    @update_once
    def up_resp_rdy():
      s.master.resp.rdy @= (s.resp_entry is None)

    @update_once
    def up_resp_msg():
      if (s.resp_entry is None) & s.master.resp.val:
        s.resp_entry = clone_deepcopy( s.master.resp.msg )

    s.add_constraints( U( up_clear_req ) < M(s.read),
                       U( up_clear_req ) < M(s.write),
                       U( up_clear_req ) < M(s.amo),

                       M( s.read )    < U( up_send_req ),
                       M( s.write )   < U( up_send_req ),
                       M( s.amo )     < U( up_send_req ),

                       M( s.read )      < U( up_resp_rdy ),
                       M( s.write )     < U( up_resp_rdy ),
                       M( s.amo )       < U( up_resp_rdy ),
                       U( up_resp_rdy ) < U( up_resp_msg ) )

class XcelMasterAdapter( Component ):

  @blocking
  def read( s, addr ):
    while s.req_entry is not None:
      greenlet.getcurrent().parent.switch(0)

    s.req_entry = s.create_req( 0, addr )

    while s.resp_entry is None:
      greenlet.getcurrent().parent.switch(0)

    ret = s.resp_entry.data
    s.resp_entry = None
    return ret

  @blocking
  def write( s, addr, data ):
    while s.req_entry is not None:
      greenlet.getcurrent().parent.switch(0)

    s.req_entry = s.create_req( 1, addr, data )

    while s.resp_entry is None:
      greenlet.getcurrent().parent.switch(0)

    s.resp_entry = None

  def construct( s, ReqType, RespType ):
    s.master = MasterIfcRTL( ReqType, RespType )

    # Use create_req to handle type mismatch
    Tdata = ReqType.get_field_type('data')
    s.create_req = lambda a,b,c=0: ReqType( a, b, Tdata(int(c)) )

    s.req_entry  = None
    s.resp_entry = None

    # req path

    s.req_sent = Wire()

    @update_ff
    def up_req_sent():
      s.req_sent <<= s.master.req.val & s.master.req.rdy

    @update
    def up_clear_req():
      if s.req_sent:
        s.req_entry = None

    @update_once
    def up_send_req():
      if s.req_entry is None:
        s.master.req.val @= 0
      else:
        s.master.req.val @= 1
        s.master.req.msg @= s.req_entry

    # resp path
    @update_once
    def up_resp_rdy():
      s.master.resp.rdy @= (s.resp_entry is None)

    @update_once
    def up_resp_msg():
      if (s.resp_entry is None) & s.master.resp.val:
        s.resp_entry = clone_deepcopy( s.master.resp.msg )

    s.add_constraints( U( up_clear_req ) < M(s.read),
                       U( up_clear_req ) < M(s.write),

                       M( s.read )    < U( up_send_req ),
                       M( s.write )   < U( up_send_req ),

                       M( s.read )      < U( up_resp_rdy ),
                       M( s.write )     < U( up_resp_rdy ),
                       U( up_resp_rdy ) < U( up_resp_msg ) )
