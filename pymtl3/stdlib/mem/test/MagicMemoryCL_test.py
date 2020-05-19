#=========================================================================
# TestMemory_test.py
#=========================================================================

import random
import struct

import pytest

from pymtl3 import *
from pymtl3.stdlib.test_utils import TestSinkCL, TestSrcCL, mk_test_case_table, run_sim

from ..MagicMemoryCL import MagicMemoryCL
from ..MemMsg import MemMsgType, mk_mem_msg

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, cls, nports, PortTypes, src_msgs, sink_msgs,
                 stall_prob, mem_latency, src_initial,  src_interval, sink_initial, sink_interval,
                 arrival_time=None ):
    assert len(PortTypes) == nports
    s.srcs = [ TestSrcCL( PortTypes[i][0], src_msgs[i], src_initial, src_interval )
                for i in range(nports) ]
    s.mem  = cls( nports, PortTypes, stall_prob, mem_latency )
    s.sinks = [ TestSinkCL( PortTypes[i][1], sink_msgs[i], sink_initial, sink_interval,
                            arrival_time ) for i in range(nports) ]

    # Connections
    for i in range(nports):
      connect( s.srcs[i].send, s.mem.ifc[i].req )
      connect( s.mem.ifc[i].resp,  s.sinks[i].recv  )

  def done( s ):
    return all([x.done() for x in s.srcs] + [x.done() for x in s.sinks])

  def line_trace( s ):
    return "{} >>>  {}  >>> {}".format(
      "|".join( [ x.line_trace() for x in s.srcs ] ),
      s.mem.line_trace(),
      "|".join( [ x.line_trace() for x in s.sinks ] ) )

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

req_type_dict = {
  'rd': MemMsgType.READ,
  'wr': MemMsgType.WRITE,
  'ad': MemMsgType.AMO_ADD,
  'an': MemMsgType.AMO_AND,
  'or': MemMsgType.AMO_OR,
  'xg': MemMsgType.AMO_SWAP,
  'mn': MemMsgType.AMO_MIN,
}

resp_type_dict = {
  'rd': MemMsgType.READ,
  'wr': MemMsgType.WRITE,
  'ad': MemMsgType.AMO_ADD,
  'an': MemMsgType.AMO_AND,
  'or': MemMsgType.AMO_OR,
  'xg': MemMsgType.AMO_SWAP,
  'mn': MemMsgType.AMO_MIN,
}

req_cls, resp_cls = mk_mem_msg( 8, 32, 32 )

def req( type_, opaque, addr, len, data ):
  return req_cls( req_type_dict[type_], opaque, addr, len, b32(data) )

def resp( type_, opaque, len, data ):
  return resp_cls( resp_type_dict[type_], opaque, 0, len, b32(data) )

#----------------------------------------------------------------------
# Test Case: basic
#----------------------------------------------------------------------

def basic_msgs( base_addr ):
  return [
    req( 'wr', 0x0, base_addr, 0, 0xdeadbeef ), resp( 'wr', 0x0, 0, 0          ),
    req( 'rd', 0x1, base_addr, 0, 0          ), resp( 'rd', 0x1, 0, 0xdeadbeef ),
  ]

#----------------------------------------------------------------------
# Test Case: stream
#----------------------------------------------------------------------

def stream_msgs( base_addr ):

  msgs = []
  for i in range(20):
    msgs.extend([
      req( 'wr', i, base_addr+4*i, 0, i ), resp( 'wr', i, 0, 0 ),
      req( 'rd', i, base_addr+4*i, 0, 0 ), resp( 'rd', i, 0, i ),
    ])

  return msgs

#----------------------------------------------------------------------
# Test Case: subword reads
#----------------------------------------------------------------------

def subword_rd_msgs( base_addr ):
  return [

    req( 'wr', 0x0, base_addr+0, 0, 0xdeadbeef ), resp( 'wr', 0x0, 0, 0          ),

    req( 'rd', 0x1, base_addr+0, 1, 0          ), resp( 'rd', 0x1, 1, 0x000000ef ),
    req( 'rd', 0x2, base_addr+1, 1, 0          ), resp( 'rd', 0x2, 1, 0x000000be ),
    req( 'rd', 0x3, base_addr+2, 1, 0          ), resp( 'rd', 0x3, 1, 0x000000ad ),
    req( 'rd', 0x4, base_addr+3, 1, 0          ), resp( 'rd', 0x4, 1, 0x000000de ),

    req( 'rd', 0x5, base_addr+0, 2, 0          ), resp( 'rd', 0x5, 2, 0x0000beef ),
    req( 'rd', 0x6, base_addr+1, 2, 0          ), resp( 'rd', 0x6, 2, 0x0000adbe ),
    req( 'rd', 0x7, base_addr+2, 2, 0          ), resp( 'rd', 0x7, 2, 0x0000dead ),

    req( 'rd', 0x8, base_addr+0, 3, 0          ), resp( 'rd', 0x8, 3, 0x00adbeef ),
    req( 'rd', 0x9, base_addr+1, 3, 0          ), resp( 'rd', 0x9, 3, 0x00deadbe ),

    req( 'rd', 0xa, base_addr+0, 0, 0          ), resp( 'rd', 0xa, 0, 0xdeadbeef ),

  ]

#----------------------------------------------------------------------
# Test Case: subword writes
#----------------------------------------------------------------------

def subword_wr_msgs( base_addr ):
  return [

    req( 'wr', 0x0, base_addr+0, 1, 0x000000ef ), resp( 'wr', 0x0, 0, 0          ),
    req( 'wr', 0x1, base_addr+1, 1, 0x000000be ), resp( 'wr', 0x1, 0, 0          ),
    req( 'wr', 0x2, base_addr+2, 1, 0x000000ad ), resp( 'wr', 0x2, 0, 0          ),
    req( 'wr', 0x3, base_addr+3, 1, 0x000000de ), resp( 'wr', 0x3, 0, 0          ),
    req( 'rd', 0x4, base_addr+0, 0, 0          ), resp( 'rd', 0x4, 0, 0xdeadbeef ),

    req( 'wr', 0x5, base_addr+0, 2, 0x0000abcd ), resp( 'wr', 0x5, 0, 0          ),
    req( 'wr', 0x6, base_addr+2, 2, 0x0000ef01 ), resp( 'wr', 0x6, 0, 0          ),
    req( 'rd', 0x7, base_addr+0, 0, 0          ), resp( 'rd', 0x7, 0, 0xef01abcd ),

    req( 'wr', 0x8, base_addr+1, 2, 0x00002345 ), resp( 'wr', 0x8, 0, 0          ),
    req( 'rd', 0xa, base_addr+0, 0, 0          ), resp( 'rd', 0xa, 0, 0xef2345cd ),

    req( 'wr', 0xb, base_addr+0, 3, 0x00cafe02 ), resp( 'wr', 0xb, 0, 0          ),
    req( 'rd', 0xc, base_addr+0, 0, 0          ), resp( 'rd', 0xc, 0, 0xefcafe02 ),

  ]

#----------------------------------------------------------------------
# Test Case: amos
#----------------------------------------------------------------------

def amo_msgs( base_addr ):
  return [
    # load some initial data
    req( 'wr', 0x0, base_addr   , 0, 0x01234567 ), resp( 'wr', 0x0, 0, 0          ),
    req( 'wr', 0x0, base_addr+4 , 0, 0x98765432 ), resp( 'wr', 0x0, 0, 0          ),
    req( 'wr', 0x0, base_addr+8 , 0, 0x22002200 ), resp( 'wr', 0x0, 0, 0          ),
    req( 'wr', 0x0, base_addr+12, 0, 0x00112233 ), resp( 'wr', 0x0, 0, 0          ),
    req( 'wr', 0x0, base_addr+16, 0, 0x44556677 ), resp( 'wr', 0x0, 0, 0          ),
    req( 'wr', 0x0, base_addr+20, 0, 0x01230123 ), resp( 'wr', 0x0, 0, 0          ),
    # amo.add
    req( 'ad', 0x1, base_addr   , 0, 0x12345678 ), resp( 'ad', 0x1, 0, 0x01234567 ),
    req( 'rd', 0x2, base_addr   , 0, 0          ), resp( 'rd', 0x2, 0, 0x13579bdf ),
    # amo.and
    req( 'an', 0x3, base_addr+4 , 0, 0x23456789 ), resp( 'an', 0x3, 0, 0x98765432 ),
    req( 'rd', 0x4, base_addr+4 , 0, 0          ), resp( 'rd', 0x4, 0, 0x00444400 ),
    # amo.or
    req( 'or', 0x5, base_addr+8 , 0, 0x01230123 ), resp( 'or', 0x5, 0, 0x22002200 ),
    req( 'rd', 0x6, base_addr+8 , 0, 0          ), resp( 'rd', 0x6, 0, 0x23232323 ),
    # amo.xchg
    req( 'xg', 0x5, base_addr+12, 0, 0xdeadbeef ), resp( 'xg', 0x5, 0, 0x00112233 ),
    req( 'rd', 0x6, base_addr+12, 0, 0          ), resp( 'rd', 0x6, 0, 0xdeadbeef ),
    # amo.min -- mem is smaller
    req( 'mn', 0x7, base_addr+16, 0, 0xcafebabe ), resp( 'mn', 0x7, 0, 0x44556677 ),
    req( 'rd', 0x8, base_addr+16, 0, 0          ), resp( 'rd', 0x8, 0, 0xcafebabe ),
    # amo.min -- arg is smaller
    req( 'mn', 0x9, base_addr+20, 0, 0x01201234 ), resp( 'mn', 0x9, 0, 0x01230123 ),
    req( 'rd', 0xa, base_addr+20, 0, 0          ), resp( 'rd', 0xa, 0, 0x01201234 ),
  ]

#----------------------------------------------------------------------
# Test Case: random
#----------------------------------------------------------------------

def random_msgs( base_addr ):

  rgen = random.Random()
  rgen.seed(0xa4e28cc2)

  vmem = [ rgen.randint(0,0xffffffff) for _ in range(20) ]
  msgs = []

  for i in range(20):
    msgs.extend([
      req( 'wr', i, base_addr+4*i, 0, vmem[i] ), resp( 'wr', i, 0, 0 ),
    ])

  for i in range(1):
    idx = rgen.randint(0,19)

    if rgen.randint(0,1):

      correct_data = vmem[idx]
      msgs.extend([
        req( 'rd', i, base_addr+4*idx, 0, 0 ), resp( 'rd', i, 0, correct_data ),
      ])

    else:

      new_data = rgen.randint(0,0xffffffff)
      vmem[idx] = new_data
      msgs.extend([
        req( 'wr', i, base_addr+4*idx, 0, new_data ), resp( 'wr', i, 0, 0 ),
      ])

  return msgs

#-------------------------------------------------------------------------
# Test Case Table
#-------------------------------------------------------------------------

test_case_table = mk_test_case_table([
  (                             "msg_func          stall lat src_init src_intv sink_init sink_intv"),
  [ "basic",                     basic_msgs,       0.0,  1,  0,       0,       0,        0         ],
  [ "stream",                    stream_msgs,      0.0,  1,  0,       0,       0,        0         ],
  [ "subword_rd",                subword_rd_msgs,  0.0,  1,  0,       0,       0,        0         ],
  [ "subword_wr",                subword_wr_msgs,  0.0,  1,  0,       0,       0,        0         ],
  [ "amo",                       amo_msgs,         0.0,  1,  0,       0,       0,        0         ],
  [ "random",                    random_msgs,      0.0,  1,  0,       0,       0,        0         ],
  [ "random_3x14",               random_msgs,      0.0,  1,  5,       3,       7,        14        ],
  [ "stream_stall0.5_lat0",      stream_msgs,      0.5,  1,  0,       0,       0,        0         ],
  [ "stream_stall0.0_lat4",      stream_msgs,      0.0,  4,  0,       0,       0,        0         ],
  [ "stream_stall0.5_lat4",      stream_msgs,      0.5,  4,  0,       0,       0,        0         ],
  [ "random_stall0.5_lat4_3x14", random_msgs,      0.5,  4,  5,       14,      7,        14        ],
])

#-------------------------------------------------------------------------
# Test cases for 1 port
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table )
def test_1port( test_params, cmdline_opts ):
  msgs = test_params.msg_func(0x1000)
  run_sim( TestHarness( MagicMemoryCL, 1, [(req_cls, resp_cls)],
                        [ msgs[::2] ],
                        [ msgs[1::2] ],
                        test_params.stall, test_params.lat,
                        test_params.src_init, test_params.src_intv,
                        test_params.sink_init, test_params.sink_intv ) )

#-------------------------------------------------------------------------
# Test cases for 2 port
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table )
def test_2port( test_params, cmdline_opts ):
  msgs0 = test_params.msg_func(0x1000)
  msgs1 = test_params.msg_func(0x2000)
  run_sim( TestHarness( MagicMemoryCL, 2, [(req_cls, resp_cls)]*2,
                        [ msgs0[::2],  msgs1[::2]  ],
                        [ msgs0[1::2], msgs1[1::2] ],
                        test_params.stall, test_params.lat,
                        test_params.src_init, test_params.src_intv,
                        test_params.sink_init, test_params.sink_intv ) )

@pytest.mark.parametrize( **test_case_table )
def test_20port( test_params, cmdline_opts ):
  msgs = [ test_params.msg_func(0x1000*i) for i in range(20) ]
  run_sim( TestHarness( MagicMemoryCL, 20, [(req_cls, resp_cls)]*20,
                        [ x[::2]  for x in msgs ],
                        [ x[1::2] for x in msgs ],
                        test_params.stall, test_params.lat,
                        test_params.src_init, test_params.src_intv,
                        test_params.sink_init, test_params.sink_intv ) )

#-------------------------------------------------------------------------
# Test Read/Write Mem
#-------------------------------------------------------------------------

def test_read_write_mem( cmdline_opts ):

  rgen = random.Random()
  rgen.seed(0x05a3e95b)

  # Test data we want to write into memory

  data = [ rgen.randrange(-(2**31),2**31) for _ in range(20) ]

  # Convert test data into byte array

  data_bytes = struct.pack("<{}i".format(len(data)),*data)

  # Create memory messages to read and verify memory contents

  msgs = []
  for i, item in enumerate(data):
    msgs.extend([
      req( 'rd', 0x1, 0x1000+4*i, 0, 0 ), resp( 'rd', 0x1, 0, item ),
    ])

  # Create test harness with above memory messages

  th = TestHarness( MagicMemoryCL, 2, [(req_cls, resp_cls)]*2, [msgs[::2], []], [msgs[1::2], []],
                    0, 0, 0, 0, 0, 0 )
  th.elaborate()

  # Write the data into the test memory

  th.mem.write_mem( 0x1000, data_bytes )

  # Run the test

  run_sim( th )

  # Read the data back out of the test memory

  result_bytes = th.mem.read_mem( 0x1000, len(data_bytes) )

  # Convert result bytes into list of ints

  result = list(struct.unpack("<{}i".format(len(data)),result_bytes))

  # Compare result to original data

  assert result == data
