#=========================================================================
# ReorderQueue_test.py
#=========================================================================

from pymtl3 import *
from pymtl3.passes.backends.verilog import VerilogTranslationImportPass, \
                                           VerilogVerilatorImportPass, \
                                           VerilogPlaceholderPass
from pymtl3.stdlib.test_utils.test_sinks import TestSinkRTL
from pymtl3.stdlib.mem import mk_mem_req_msg

from ..ReorderQueue import ReorderQueue
from ..ReorderQueueHost import ReorderQueueHost
from ..RandomDelayQueue import RandomDelayQueue

class TestHarness( Component ):

  def construct( s, MsgType, num_elems, num_reqs, salt, sink_msgs ):

    s.host = ReorderQueueHost( MsgType, num_elems, num_reqs )
    s.loop = RandomDelayQueue( MsgType, salt )
    s.dut  = ReorderQueue( MsgType, num_elems )
    s.sink = TestSinkRTL( MsgType, sink_msgs )

    # Connections

    s.reorder_q_deq = Wire()
    s.reorder_q_deq //= lambda: s.dut.deq.en & s.dut.deq.rdy

    s.host.deq //= s.loop.enq
    s.host.reorder_q_deq_go //= s.reorder_q_deq

    s.loop.deq //= s.dut.enq

    s.dut.deq //= s.sink.recv

  def done( s ):
    return s.sink.done()

  def line_trace( s ):
    return f"{s.loop.line_trace()} | {s.dut.line_trace()}"

def run_test( th, cmdline_opts ):
  th.elaborate()
  if cmdline_opts['test_verilog']:
    th.dut.set_metadata( VerilogTranslationImportPass.enable, True )
    if cmdline_opts['dump_vcd']:
      th.dut.set_metadata( VerilogVerilatorImportPass.vl_trace, True )
    th.apply( VerilogPlaceholderPass() )
    th.apply( VerilogTranslationImportPass() )
  th.apply( DefaultPassGroup() )
  th.sim_reset()

  curT, maxT = 0, 1000

  # DUT operation
  while not th.done() and curT < maxT:
    th.sim_tick()
    curT += 1

  assert curT < maxT, "Time out!"

def gen_sink_msgs( MsgType, num_elems, num_reqs, salt ):
  msgs = []
  for i in range(num_reqs):
    msg        = MsgType()
    msg.type_  @= 1
    msg.addr   @= 4*i
    msg.data   @= salt + i
    msg.opaque @= i%num_elems
    msgs.append(msg)
  return msgs

def test_simple_4( cmdline_opts ):
  o, a, d = 2, 20, 32
  num_elems = 4
  num_reqs = 32
  salt = 0xfaceb00c
  MsgType = mk_mem_req_msg( o, a, d )
  sink_msgs = gen_sink_msgs( MsgType, num_elems, num_reqs, salt )
  run_test( TestHarness( MsgType, num_elems, num_reqs, salt, sink_msgs ),
            cmdline_opts)

def test_simple_32( cmdline_opts ):
  o, a, d = 5, 20, 32
  num_elems = 32
  num_reqs = 256
  salt = 0xfaceb00c
  MsgType = mk_mem_req_msg( o, a, d )
  sink_msgs = gen_sink_msgs( MsgType, num_elems, num_reqs, salt )
  run_test( TestHarness( MsgType, num_elems, num_reqs, salt, sink_msgs ),
            cmdline_opts)
