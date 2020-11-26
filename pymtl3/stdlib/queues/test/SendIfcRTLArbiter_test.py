#=========================================================================
# SendIfcRTLArbiter_test.py
#=========================================================================

from random import seed, randrange

from pymtl3 import *
from pymtl3.passes.backends.verilog import VerilogTranslationImportPass, \
                                           VerilogVerilatorImportPass, \
                                           VerilogPlaceholderPass
from pymtl3.stdlib.test_utils import TestSinkCL, TestSrcCL

from ..SendIfcRTLArbiter import SendIfcRTLArbiter

seed(0xfaceb00c)

class TestHarness( Component ):

  def construct( s, MsgType, ninputs, src_msgs, sink_msgs, src_delay, sink_delay ):

    s.dut = SendIfcRTLArbiter( MsgType, ninputs )
    s.srcs = [ TestSrcCL( MsgType, msgs, interval_delay=src_delay ) for msgs in src_msgs ]
    s.sink = TestSinkCL( MsgType, sink_msgs, interval_delay=sink_delay )

    for i in range(ninputs):
      s.dut.recv[i] //= s.srcs[i].send
    s.dut.send //= s.sink.recv

  def done( s ):
    return all(src.done() for src in s.srcs) and s.sink.done()

  def line_trace( s ):
    return s.dut.line_trace()

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

def gen_msgs( Type, ninputs, num_messages ):
  type_nbits = Type.nbits
  HalfType = mk_bits(type_nbits // 2)
  src_msgs, sink_msgs = [], []
  src_prefix = []

  # Generate source masks

  for i in range(ninputs):
    prefix = mk_bits(type_nbits // 2)(i)
    src_prefix.append( prefix )

  # Generate source messages

  for i in range(ninputs):
    msgs = []
    for _ in range(num_messages):
      data = concat( src_prefix[i], HalfType(randrange(0, 2**(type_nbits//2))) )
      msgs.append( data )
    src_msgs.append( msgs )

  # Generate sink messages

  for data_bundle in zip(*src_msgs):
    for data in data_bundle:
      sink_msgs.append( data )

  return src_msgs, sink_msgs

def test_simple_2( cmdline_opts ):
  MsgType = Bits32
  ninputs = 2
  num_messages = 5
  src_msgs, sink_msgs = gen_msgs( MsgType, ninputs, num_messages )
  run_test( TestHarness( MsgType, ninputs, src_msgs, sink_msgs, 2, 2 ), cmdline_opts )

def test_simple_4( cmdline_opts ):
  MsgType = Bits32
  ninputs = 4
  num_messages = 10
  src_msgs, sink_msgs = gen_msgs( MsgType, ninputs, num_messages )
  run_test( TestHarness( MsgType, ninputs, src_msgs, sink_msgs, 0, 0 ), cmdline_opts )

def test_simple_8( cmdline_opts ):
  MsgType = Bits32
  ninputs = 8
  num_messages = 20
  src_msgs, sink_msgs = gen_msgs( MsgType, ninputs, num_messages )
  run_test( TestHarness( MsgType, ninputs, src_msgs, sink_msgs, 3, 2 ), cmdline_opts )
