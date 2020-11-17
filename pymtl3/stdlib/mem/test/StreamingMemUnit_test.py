#=========================================================================
# StreamingMemUnit_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Nov 10, 2020

import pytest

from pymtl3 import *
from pymtl3.stdlib.mem import mk_mem_msg, MagicMemoryRTL

from pymtl3.passes.backends.verilog import VerilogTranslationImportPass, \
                                           VerilogVerilatorImportPass, \
                                           VerilogPlaceholderPass
from pymtl3.stdlib.test_utils import TestSinkCL, TestSrcCL

from .StreamingMemUnitHost import StreamingMemUnitHost
from ..StreamingMemUnit import StreamingMemUnit, mk_smu_msg

# Padding Directions
W = 0
E = 1
N = 2
S = 3

class TestHarness( Component ):

  def construct( s, DataType, AddrType, StrideType, CountType, OpaqueType,
                 padding, src_base_addr, src_x_stride, src_x_count,
                 src_y_stride, src_y_count, dst_base_addr, dst_ack_addr,
                 sink_msgs, mem_image ):

    s.mem_image = mem_image

    s.addr_nbits = AddrType.nbits
    s.opaque_nbits = OpaqueType.nbits

    ReqMsgType, RespMsgType = mk_mem_msg( s.opaque_nbits, AddrType.nbits, DataType.nbits )
    SMUReqType, SMURespType = mk_smu_msg( s.opaque_nbits, AddrType.nbits, DataType.nbits )

    s.dut = StreamingMemUnit( DataType, AddrType, StrideType, CountType, OpaqueType )
    s.mem = MagicMemoryRTL( 1, [(ReqMsgType, RespMsgType)] )
    s.host = StreamingMemUnitHost( DataType, AddrType, StrideType, CountType,
                                   padding, src_base_addr, src_x_stride,
                                   src_x_count, src_y_stride,
                                   src_y_count, dst_base_addr, dst_ack_addr )

    s.local_req_sink = TestSinkCL( SMUReqType, sink_msgs )
    s.local_resp_src = TestSrcCL( SMURespType, [] )

    s.dut.cfg //= s.host.cfg
    s.dut.local.req //= s.local_req_sink.recv
    s.dut.local.resp //= s.local_resp_src.send

    @update
    def smu_th_mem_adapter():
      # Request
      s.mem.ifc[0].req.en         @= s.dut.remote.req.en
      s.dut.remote.req.rdy        @= s.mem.ifc[0].req.rdy
      s.mem.ifc[0].req.msg.type_  @= zext( s.dut.remote.req.msg.wen, 4 )
      s.mem.ifc[0].req.msg.opaque @= s.dut.remote.req.msg.reg_id
      s.mem.ifc[0].req.msg.addr   @= s.dut.remote.req.msg.addr
      s.mem.ifc[0].req.msg.len    @= 0
      s.mem.ifc[0].req.msg.data   @= s.dut.remote.req.msg.data

      # Response
      s.dut.remote.resp.en         @= s.mem.ifc[0].resp.en
      s.mem.ifc[0].resp.rdy        @= s.dut.remote.resp.rdy
      s.dut.remote.resp.msg.wen    @= s.mem.ifc[0].resp.msg.type_[0]
      s.dut.remote.resp.msg.reg_id @= s.mem.ifc[0].resp.msg.opaque
      s.dut.remote.resp.msg.opaque @= 0
      s.dut.remote.resp.msg.data   @= s.mem.ifc[0].resp.msg.data

  def load_mem_image( s ):
    for i in range(2**s.addr_nbits-1):
      s.mem.write_mem( i, [s.mem_image[i]] )

  def done( s ):
    return s.local_req_sink.done() and s.local_resp_src.done()

  def line_trace( s ):
    return s.dut.line_trace() + " || " + s.local_req_sink.line_trace()

def get_mem_word( image, addr ):
  assert addr % 4 == 0, "address has to be word-aligned!"
  byte_arr = image[addr:addr+4]
  data = 0
  for i in range(3, -1, -1):
    data = data << 8
    data = data | byte_arr[i]
  return Bits32(data)

def gen_mem_image( pattern, *args ):
  image = []
  addr_nbits = args[0]
  if pattern == 'word-increment':
    num_words = 2**(addr_nbits-2)
    for word_idx in range(num_words):
      word = word_idx
      for byte_idx in range(4):
        byte = word & 0xFF
        word = word >> 8
        image.append(byte)
  elif pattern == 'byte-increment':
    for i in range(2**addr_nbits):
      image.append( i % 256 )
  else:
    raise NotImplementedError
  return image

def gen_sink_msgs( image, O, A, D, padding, s_base, x_stride, x_count,
                   y_stride, y_count, d_base, d_ack_addr ):
  msgs = []
  dst_addr = d_base
  MsgType, _ = mk_smu_msg( O, A, D )
  MaxOpaque = 2**O

  row_addr = s_base
  cnt = 0
  for y in range(y_count):
    for x in range(x_count):
      is_padding = False
      if (padding[W] & (x == 0)) | (padding[E] & (x == (x_count-1))) | \
         (padding[N] & (y == 0)) | (padding[S] & (y == (y_count-1))):
        is_padding = True

      addr = row_addr + x * x_stride
      word = get_mem_word( image, addr )

      msg        = MsgType()
      msg.wen    = Bits1(1)
      msg.reg_id = mk_bits(O)(cnt % MaxOpaque)
      msg.opaque = Bits1(0)
      msg.addr   = mk_bits(A)(dst_addr)
      msg.data   = mk_bits(D)(word) if not is_padding else mk_bits(D)(0)

      msgs.append( msg )
      dst_addr += 4
      cnt += 1

    row_addr += y_stride

  # Append ack message

  msg        = MsgType()
  msg.wen    = Bits1(1)
  msg.reg_id = mk_bits(O)(0)
  msg.opaque = Bits1(0)
  msg.addr   = mk_bits(A)(d_ack_addr)
  msg.data   = mk_bits(D)(1)

  msgs.append( msg )

  return msgs

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

  th.load_mem_image()

  curT, maxT = 0, 300

  # DUT operation
  while not th.done() and curT < maxT:
    th.sim_tick()
    # print(th.dut.line_trace())
    curT += 1

  assert curT < maxT, "Time out!"

@pytest.mark.parametrize(
    "padding", [Bits4(x) for x in range(2**4)]
)
def test_simple_byte_increment( cmdline_opts, padding ):
  O, D, A, S, C = Bits5, Bits32, Bits20, Bits10, Bits10
  Types = [ D, A, S, C, O ]

  src_base_addr = 0
  src_x_stride = 4
  src_x_count = 16
  src_y_stride = 64*4
  src_y_count = 16
  dst_base_addr = 0
  dst_ack_addr = 2048

  Params = [padding, src_base_addr, src_x_stride, src_x_count,
            src_y_stride, src_y_count, dst_base_addr, dst_ack_addr]

  image = gen_mem_image( 'byte-increment', A.nbits )

  sink_msgs = gen_sink_msgs( image,
                             O.nbits, A.nbits, D.nbits,
                             padding, src_base_addr,
                             src_x_stride, src_x_count,
                             src_y_stride, src_y_count,
                             dst_base_addr, dst_ack_addr )

  run_test( TestHarness( *Types, *Params, sink_msgs, image ), cmdline_opts )

@pytest.mark.parametrize(
    "padding", [Bits4(x) for x in range(2**4)]
)
def test_simple_word_increment( cmdline_opts, padding ):
  O, D, A, S, C = Bits5, Bits32, Bits20, Bits10, Bits10
  Types = [ D, A, S, C, O ]

  src_base_addr = 0
  src_x_stride = 4
  src_x_count = 16
  src_y_stride = 64*4
  src_y_count = 16
  dst_base_addr = 0
  dst_ack_addr = 2048

  Params = [padding, src_base_addr, src_x_stride, src_x_count,
            src_y_stride, src_y_count, dst_base_addr, dst_ack_addr]

  image = gen_mem_image( 'word-increment', A.nbits )

  sink_msgs = gen_sink_msgs( image,
                             O.nbits, A.nbits, D.nbits,
                             padding, src_base_addr,
                             src_x_stride, src_x_count,
                             src_y_stride, src_y_count,
                             dst_base_addr, dst_ack_addr )

  run_test( TestHarness( *Types, *Params, sink_msgs, image ), cmdline_opts )
