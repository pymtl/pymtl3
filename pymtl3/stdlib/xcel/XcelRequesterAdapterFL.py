import greenlet

from pymtl3 import *
from pymtl3.extra import clone_deepcopy
from pymtl3.stdlib.reqresp.ifcs import RequesterIfc

class XcelRequesterAdapterFL( Component ):

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
    s.requester = RequesterIfc( ReqType, RespType )

    # Use create_req to handle type mismatch
    Tdata = ReqType.get_field_type('data')
    s.create_req = lambda a,b,c=0: ReqType( a, b, Tdata(int(c)) )

    s.req_entry  = None
    s.resp_entry = None

    # req path

    s.req_sent = Wire()

    @update_ff
    def up_req_sent():
      s.req_sent <<= s.requester.req.val & s.requester.req.rdy

    @update
    def up_clear_req():
      if s.req_sent:
        s.req_entry = None

    @update_once
    def up_send_req():
      if s.req_entry is None:
        s.requester.req.val @= 0
      else:
        s.requester.req.val @= 1
        s.requester.req.msg @= s.req_entry

    # resp path
    @update_once
    def up_resp_rdy():
      s.requester.rsp.rdy @= (s.resp_entry is None)

    @update_once
    def up_resp_msg():
      if (s.resp_entry is None) & s.requester.rsp.val:
        s.resp_entry = clone_deepcopy( s.requester.rsp.msg )

    s.add_constraints( U( up_clear_req ) < M(s.read),
                       U( up_clear_req ) < M(s.write),

                       M( s.read )    < U( up_send_req ),
                       M( s.write )   < U( up_send_req ),

                       M( s.read )      < U( up_resp_rdy ),
                       M( s.write )     < U( up_resp_rdy ),
                       U( up_resp_rdy ) < U( up_resp_msg ) )
