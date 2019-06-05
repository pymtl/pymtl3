"""
==========================================================================
 xcel_ifcs_test.py
==========================================================================

Author : Yanghui Ou
  Date : June 4, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.stdlib.ifcs import XcelMsgType, mk_xcel_msg
from pymtl3.stdlib.rtl import RegisterFile
from pymtl3.stdlib.rtl.queues import NormalQueueRTL

from .xcel_ifcs import (
    XcelMasterIfcCL,
    XcelMasterIfcFL,
    XcelMinionIfcCL,
    XcelMinionIfcRTL,
)

#=========================================================================
# FL-CL composition
#=========================================================================

def test_xcel_fl_cl_adapter():

  class SomeMasterFL( Component ):
    def construct( s, nregs=1, has_loop=False ):
      s.xcel = XcelMasterIfcFL()

      s.addr = 0
      s.nregs = nregs
      s.trace = ""

      if has_loop:
        @s.update
        def up_master_while():
          s.trace = "             "
          while s.addr < s.nregs:
            wr_data = 0xbabe0000 | s.addr
            s.xcel.write( s.addr, wr_data )
            s.trace = "wr:{:x}:{:x}".format( s.addr, wr_data )
            rd_data = s.xcel.read( s.addr )
            s.trace = "rd:{:x}:{:x}".format( s.addr, rd_data )
            s.addr += 1
      else:
        @s.update
        def up_master_noloop():
          s.trace = "#            "
          wr_data = 0xbabe0000 | s.addr
          s.xcel.write( s.addr, wr_data )
          s.trace = "wr:{:x}:{:x}".format( s.addr, wr_data )
          rd_data = s.xcel.read( s.addr )
          s.trace = "rd:{:x}:{:x}".format( s.addr, rd_data )
          s.addr += 1

    def done( s ):
      return s.addr >= s.nregs

    def line_trace( s ):
      return s.trace

  class SomeMinionCL( Component ):

    def recv( s, msg ):
      assert s.entry is None
      s.entry = msg

    def recv_rdy( s ):
      return s.entry is None

    def read( s, addr ):
      addr = int(addr)
      return s.reg_file[ addr ]

    def write( s, addr, data ):
      addr = int(addr)
      s.reg_file[ addr ] = data

    def construct( s, req_class, resp_class ):
      s.xcel = XcelMinionIfcCL( req_class, resp_class, s.recv, s.recv_rdy )
      s.entry = None

      s.reg_file = [ 0 for _ in range(16) ]

      @s.update
      def up_process():

        if s.entry is not None and s.xcel.resp.rdy():

          # Dequeue xcel request message

          req     = s.entry
          s.entry = None

          if req.type_ == XcelMsgType.READ:
            resp = resp_class( req.type_, s.read( req.addr ) )

          elif req.type_ == XcelMsgType.WRITE:
            s.write( req.addr, req.data )
            resp = resp_class( req.type_, 0 )

          s.xcel.resp( resp )

      s.add_constraints( U(up_process) < M(s.xcel.req) ) # pipeline behavior

    def line_trace( s ):
      return s.xcel.line_trace()

  class TestHarness( Component ):
    def construct( s ):
      s.master = [ SomeMasterFL( i*5, i ) for i in range(2) ]
      s.minion = [ SomeMinionCL( *mk_xcel_msg(4,32) )( xcel = s.master[i].xcel )
                    for i in range(2) ]

    def line_trace( s ):
      return "|".join( [ x.line_trace() for x in s.master ] ) + " >>> " + \
             "|".join( [ x.line_trace() for x in s.minion ] )

    def done( s ):
      return all( [ x.done() for x in s.master ] )

  th = TestHarness()

  # Create a simulator

  th.apply( SimpleSim )

  # Run simulation

  print("")
  ncycles = 0
  while not th.done() and ncycles < 1000:
    th.tick()
    ncycles += 1
    trace = th.line_trace()
    print("{:3}: {}".format( ncycles, trace ))

  # Check timeout

  assert ncycles < 1000

  th.tick()
  th.tick()
  th.tick()

#=========================================================================
# CL-RTL composition
#=========================================================================

def test_xcel_cl_rtl():

  class SomeMasterCL( Component ):
    def recv( s, msg ):
      if msg.type_ == XcelMsgType.READ:
        assert msg.data == 0xface0000 | s.addr-1
        s.count += 1

    def recv_rdy( s ):
      return True

    def construct( s, ReqType, RespType, nregs=1 ):
      s.xcel = XcelMasterIfcCL( ReqType, RespType, s.recv, s.recv_rdy )
      s.addr = 0
      s.count = 0
      s.nregs = nregs
      s.flag = True

      @s.update
      def up_master_req():
        if s.xcel.req.rdy():
          if s.flag:
            s.xcel.req( ReqType( XcelMsgType.WRITE, s.addr, 0xface0000 | s.addr ) )
            s.flag = not s.flag
          else:
            s.xcel.req( ReqType( XcelMsgType.READ, s.addr, 0 ) )
            s.addr += 1
            s.flag = not s.flag

    def done( s ):
      return s.count == s.nregs

    def line_trace( s ):
      return "{}".format( s.xcel )

  class SomeMinionRTL( Component ):
    def construct( s, ReqType, RespType, nregs=2 ):

      # Interface

      s.xcel = XcelMinionIfcRTL( ReqType, RespType )
      
      # Local parameters
      
      s.data_nbits = max( ReqType.data_nbits, RespType.data_nbits )
      DataType  = mk_bits( s.data_nbits )
      s.nregs   = nregs

      # Components

      s.req_q = NormalQueueRTL( ReqType, num_entries=1 )
      s.wen   = Wire( Bits1 )
      s.reg_file = RegisterFile( DataType, nregs )(
        raddr = { 0: s.req_q.deq.msg.addr },
        rdata = { 0: s.xcel.resp.msg.data },
        wen   = { 0: s.wen                },
        waddr = { 0: s.req_q.deq.msg.addr },
        wdata = { 0: s.req_q.deq.msg.data },
      )
      s.connect( s.xcel.req,            s.req_q.enq           )
      s.connect( s.xcel.resp.msg.type_, s.req_q.deq.msg.type_ )

      @s.update
      def up_wen():
        s.wen = s.req_q.deq.rdy and s.req_q.deq.msg.type_ == XcelMsgType.WRITE

      @s.update
      def up_resp():
        s.xcel.resp.en = s.req_q.deq.rdy and s.xcel.resp.rdy
        s.req_q.deq.en = s.req_q.deq.rdy and s.xcel.resp.rdy

    def line_trace( s ):
      return "{}".format( s.xcel )

  class TestHarness( Component ):
    def construct( s ):
      Req, Resp = mk_xcel_msg( addr=4, data=32 )
      s.master = SomeMasterCL( Req, Resp, 10 )
      s.minion = SomeMinionRTL( Req, Resp, 16 )( xcel = s.master.xcel )

    def done( s ):
      return s.master.done()

    def line_trace( s ):
      return "{} >>> {}".format( s.master.line_trace(), s.minion.line_trace() )

  th = TestHarness()  

  # Create a simulator

  th.apply( SimpleSim )

  # Run simulation

  print("")
  ncycles = 0
  while not th.done() and ncycles < 1000:
    th.tick()
    ncycles += 1
    trace = th.line_trace()
    print("{:3}: {}".format( ncycles, trace ))

  # Check timeout

  assert ncycles < 1000

  th.tick()
  th.tick()
  th.tick()
