import greenlet

from pymtl3 import *
from pymtl3.extra import clone_deepcopy
from pymtl3.stdlib.mem.MemMsg import MemMsgType
from pymtl3.stdlib.reqresp.ifcs import RequesterIfc

class MemRequesterAdapterFL( Component ):

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
    s.requester = RequesterIfc( ReqType, RespType )

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
      s.req_sent <<= s.requester.reqstream.val & s.requester.reqstream.rdy

    @update
    def up_clear_req():
      if s.req_sent:
        s.req_entry = None

    @update_once
    def up_send_req():
      if s.req_entry is None:
        s.requester.reqstream.val @= 0
      else:
        s.requester.reqstream.val @= 1
        s.requester.reqstream.msg @= s.req_entry

    # resp path
    @update_once
    def up_resp_rdy():
      s.requester.respstream.rdy @= (s.resp_entry is None)

    @update_once
    def up_resp_msg():
      if (s.resp_entry is None) & s.requester.respstream.val:
        s.resp_entry = clone_deepcopy( s.requester.respstream.msg )

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
