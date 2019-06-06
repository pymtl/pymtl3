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
    XcelMasterIfcRTL,
    XcelMinionIfcCL,
    XcelMinionIfcFL,
    XcelMinionIfcRTL,
)

#=========================================================================
# FL master/minion
#=========================================================================

class SomeMasterNonBlockingFL( Component ):
  def construct( s, ReqType, RespType, nregs=16 ):
    s.xcel = XcelMasterIfcFL()

    s.addr = 0
    s.nregs = nregs
    s.trace = ""

    @s.update
    def up_master_while():
      s.trace = "             "
      while s.addr < s.nregs:
        wr_data = 0xbabe0000 | s.addr
        s.xcel.write( s.addr, wr_data )
        s.trace = "wr:{:x}:{:x}".format( s.addr, wr_data )
        rd_data = s.xcel.read( s.addr )
        assert rd_data == wr_data
        s.trace = "rd:{:x}:{:x}".format( s.addr, rd_data )
        s.addr += 1

  def done( s ):
    return s.addr >= s.nregs

  def line_trace( s ):
    return s.trace

class SomeMasterBlockingFL( Component ):
  def construct( s, ReqType, RespType, nregs=16 ):
    s.xcel = XcelMasterIfcFL()

    s.addr = 0
    s.nregs = nregs
    s.trace = ""

    @s.update
    def up_master_noloop():
      if s.addr < s.nregs:
        s.trace = "#            "
        wr_data = 0xbabe0000 | s.addr
        s.xcel.write( s.addr, wr_data )
        s.trace = "wr:{:x}:{:x}".format( s.addr, wr_data )
        rd_data = s.xcel.read( s.addr )
        assert rd_data == wr_data
        s.trace = "rd:{:x}:{:x}".format( s.addr, rd_data )
        s.addr += 1

  def done( s ):
    return s.addr >= s.nregs

  def line_trace( s ):
    return s.trace

class SomeMinionFL( Component ):
  def read_method( s, addr ):
    return s.reg_file[ int(addr) ]
  
  def write_method( s, addr, data ):
    s.reg_file[ int(addr) ] = data

  def construct( s, ReqType, RespType, nregs=16 ):
    s.xcel = XcelMinionIfcFL( s.read_method, s.write_method )
    s.reg_file = [ None for _ in range( nregs ) ]
  
  def line_trace( s ):
    return ""

#=========================================================================
# CL master/minion
#=========================================================================

class SomeMasterCL( Component ):
  def recv( s, msg ):
    if msg.type_ == XcelMsgType.READ:
      assert msg.data == 0xface0000 | s.addr-1
      s.count += 1

  def recv_rdy( s ):
    return True

  def construct( s, ReqType, RespType, nregs=16 ):
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

  def construct( s, ReqType, RespType, nregs=16 ):
    s.xcel = XcelMinionIfcCL( ReqType, RespType, s.recv, s.recv_rdy )
    s.entry = None
    s.reg_file = [ 0 for _ in range( nregs ) ]

    @s.update
    def up_process():

      if s.entry is not None and s.xcel.resp.rdy():
        # Dequeue xcel request message
        req     = s.entry
        s.entry = None

        if req.type_ == XcelMsgType.READ:
          resp = RespType( req.type_, s.read( req.addr ) )

        elif req.type_ == XcelMsgType.WRITE:
          s.write( req.addr, req.data )
          resp = RespType( req.type_, 0 )

        s.xcel.resp( resp )

    s.add_constraints( U(up_process) < M(s.xcel.req) ) # pipeline behavior

  def line_trace( s ):
    return s.xcel.line_trace()

#=========================================================================
# RTL master/minion
#=========================================================================

class SomeMinionRTL( Component ):
  def construct( s, ReqType, RespType, nregs=16 ):

    # Interface

    s.xcel = XcelMinionIfcRTL( ReqType, RespType )
    
    # Local parameters
    
    s.data_nbits = max( ReqType.data_nbits, RespType.data_nbits )
    DataType     = mk_bits( s.data_nbits )
    s.nregs      = nregs

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

#=========================================================================
# Helpers
#=========================================================================

class TestHarness( Component ):
  def construct( s, 
                 MasterType = SomeMasterBlockingFL,
                 MinionType=SomeMinionFL,
                 nregs = 16 ):
    ReqType, RespType = mk_xcel_msg( addr=clog2(nregs), data=32 )
    s.master = MasterType( ReqType, RespType, nregs=nregs )
    s.minion = MinionType( ReqType, RespType, nregs=nregs )

    s.connect( s.master.xcel, s.minion.xcel )

  def line_trace( s ):
    return "{} > {}".format( s.master.line_trace(), s.minion.line_trace() )

  def done( s ):
    return s.master.done()

  def run_sim( s, max_cycles=1000 ):
    # Run simulation
    print("")
    ncycles = 0
    while not s.done() and ncycles < 1000:
      s.tick()
      ncycles += 1
      print("{:3}: {}".format( ncycles, s.line_trace() ))

    # Check timeout
    assert ncycles < 1000

#=========================================================================
# FL-FL composition
#=========================================================================

def test_xcel_fl_fl_blocking():
  th = TestHarness()
  th.set_param( "top.construct", 
    MasterType = SomeMasterBlockingFL,
    MinionType = SomeMinionFL,
    nregs      = 16 )
  th.apply( SimpleSim )
  th.run_sim()

def test_xcel_fl_fl_nonblocking():
  th = TestHarness()
  th.set_param( "top.construct", 
    MasterType = SomeMasterNonBlockingFL,
    MinionType = SomeMinionFL,
    nregs      = 16 )
  th.apply( SimpleSim )
  th.run_sim()

#=========================================================================
# FL-CL composition
#=========================================================================

def test_xcel_fl_cl_blocking():
  th = TestHarness()
  th.set_param( "top.construct", 
    MasterType = SomeMasterBlockingFL,
    MinionType = SomeMinionCL,
    nregs      = 16 )
  th.apply( SimpleSim )
  th.run_sim()

def test_xcel_fl_cl_nonblocking():
  th = TestHarness()
  th.set_param( "top.construct", 
    MasterType = SomeMasterNonBlockingFL,
    MinionType = SomeMinionCL,
    nregs      = 16 )
  th.apply( SimpleSim )
  th.run_sim()

#=========================================================================
# CL-CL composition
#=========================================================================

def test_xcel_cl_cl():
  th = TestHarness()
  th.set_param( "top.construct", 
    MasterType = SomeMasterCL,
    MinionType = SomeMinionCL,
    nregs      = 8 )
  th.apply( SimpleSim )
  th.run_sim()

#=========================================================================
# CL-RTL composition
#=========================================================================

def test_xcel_cl_rtl():
  th = TestHarness()
  th.set_param( "top.construct", 
    MasterType = SomeMasterCL,
    MinionType = SomeMinionRTL,
    nregs      = 8 )
  th.apply( SimpleSim )
  th.run_sim()
