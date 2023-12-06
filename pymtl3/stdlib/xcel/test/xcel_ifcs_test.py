"""
==========================================================================
 xcel_ifcs_test.py
==========================================================================

Author : Yanghui Ou
  Date : June 4, 2019
"""

from pymtl3 import *
from pymtl3.stdlib.primitive import RegisterFile
from pymtl3.stdlib.xcel import XcelMsgType, mk_xcel_msg
from pymtl3.stdlib.stream import StreamNormalQueue
from pymtl3.stdlib.test_utils import run_sim

from ..ifcs.ifcs import XcelRequesterIfc, XcelResponderIfc

#-------------------------------------------------------------------------
# RTL requester/responder
#-------------------------------------------------------------------------

class SomeRequester( Component ):

  def construct( s, ReqType, RespType, nregs=16 ):

    # Interface

    s.xcel = XcelRequesterIfc( ReqType, RespType )

    # Local parameters

    DataType = ReqType.get_field_type( 'data' )
    assert DataType is RespType.get_field_type( 'data' )
    AddrType = ReqType.get_field_type( 'addr' )

    s.nregs = nregs

    # Components

    s.addr  = Wire( AddrType )
    s.count = Wire( Bits16   )
    s.flag  = Wire( Bits1    )

    @update_ff
    def up_rtl_addr():
      if s.reset:
        s.addr <<= AddrType(0)
      elif s.xcel.reqstream.val and not s.flag:
        s.addr <<= s.addr + AddrType(1)

    @update_ff
    def up_rtl_flag():
      if s.reset:
        s.flag <<= Bits1(1)
      elif s.xcel.reqstream.val:
        s.flag <<= ~s.flag

    @update_ff
    def up_rtl_count():
      if s.reset:
        s.count <<= Bits16(0)
      elif s.xcel.respstream.val and s.xcel.respstream.msg.type_ == XcelMsgType.READ:
        s.count <<= s.count + Bits16(1)

    @update
    def up_req():
      s.xcel.reqstream.val @= ~s.reset & s.xcel.reqstream.rdy
      s.xcel.reqstream.msg.type_ @= XcelMsgType.WRITE if s.flag else XcelMsgType.READ
      s.xcel.reqstream.msg.addr  @= s.addr
      s.xcel.reqstream.msg.data  @= 0xface0000 | int(s.addr)

    @update
    def up_resp():
      s.xcel.respstream.rdy @= 1

  def done( s ):
    return s.count == s.nregs

  def line_trace( s ):
    return "{}({}){}".format( s.xcel.reqstream, s.flag, s.xcel.respstream )

class SomeResponder( Component ):

  def construct( s, ReqType, RespType, nregs=16 ):

    # Interface

    s.xcel = XcelResponderIfc( ReqType, RespType )

    # Local parameters

    DataType = ReqType.get_field_type( 'data' )
    assert DataType is RespType.get_field_type( 'data' )

    s.nregs = nregs

    # Components

    s.req_q = StreamNormalQueue( ReqType, num_entries=1 )
    s.wen   = Wire( Bits1 )

    s.reg_file = m = RegisterFile( DataType, nregs )
    m.raddr[0] //= s.req_q.ostream.msg.addr
    m.rdata[0] //= s.xcel.respstream.msg.data
    m.wen[0]   //= s.wen
    m.waddr[0] //= s.req_q.ostream.msg.addr
    m.wdata[0] //= s.req_q.ostream.msg.data

    connect( s.xcel.reqstream,            s.req_q.istream           )
    connect( s.xcel.respstream.msg.type_, s.req_q.ostream.msg.type_ )

    @update
    def up_wen():
      s.wen @= s.req_q.ostream.rdy & (s.req_q.ostream.msg.type_ == XcelMsgType.WRITE)

    @update
    def up_resp():
      s.xcel.respstream.val @= s.req_q.ostream.val & s.xcel.respstream.rdy
      s.req_q.ostream.rdy @= s.req_q.ostream.val & s.xcel.respstream.rdy

  def line_trace( s ):
    return str(s.xcel)

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s,
                 MasterType = SomeRequester,
                 MinionType = SomeResponder,
                 nregs = 16 ):
    ReqType, RespType = mk_xcel_msg( addr=clog2(nregs), data=32 )
    s.master = MasterType( ReqType, RespType, nregs=nregs )
    s.minion = MinionType( ReqType, RespType, nregs=nregs )

    connect( s.master.xcel, s.minion.xcel )

  def line_trace( s ):
    return "{} > {}".format( s.master.line_trace(), s.minion.line_trace() )

  def done( s ):
    return s.master.done()

#-------------------------------------------------------------------------
# RTL-RTL composition
#-------------------------------------------------------------------------

def test_xcel_rtl_rtl():
  th = TestHarness()
  th.set_param( "top.construct",
    MasterType = SomeRequester,
    MinionType = SomeResponder,
    nregs      = 8,
  )
  run_sim( th )
