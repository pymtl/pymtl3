"""
========================================================================
MagicMemoryCL
========================================================================
A behavioral magic memory which is parameterized based on the number of
memory request/response ports. This version is a little different from
the one in pclib because we actually use the memory messages correctly
in the interface.

Author : Shunning Jiang
Date   : Feb 6, 2020
"""
from random import Random
from collections import deque

from pymtl3 import *
from pymtl3.extra import clone_deepcopy
from pymtl3.stdlib.delays import DelayPipeDeqCL, DelayPipeSendCL, StallCL

from pymtl3.stdlib.mem.MagicMemoryFL import MagicMemoryFL
from pymtl3.stdlib.mem.MemMsg import MemMsgType, mk_mem_msg
from .ifcs import MinionIfcRTL, RecvIfcRTL, SendIfcRTL
from .queues import PipeQueueRTL

# BRGTC2 custom MemMsg modified for RISC-V 32

#- - NOTE  - - - NOTE  - - - NOTE  - - - NOTE  - - - NOTE  - - - NOTE  - -
#-------------------------------------------------------------------------
# BRGTC2
#-------------------------------------------------------------------------
# The AMO implementations (and MemMsg) has been updated to match RISC-V.
#
# There is also a small fix to the AMO ops to handle signed ops. The AMO
# operations act on the bitwidth of the processor architecture, so the
# read_data from the TestMemory used with AMOs cannot just be the memory
# request message size (e.g., 128b):
#
#         read_data = Bits( s.data_nbits )
#
# It must instead be the number of bytes matching the bitwidth in the
# processor (e.g., 32b):
#
#         read_data = Bits( nbytes*8 )
#
# Otherwise for example we would be reading 128b from the memory and
# comparing that to the 32b value from the request message.
#
#-------------------------------------------------------------------------
#- - NOTE  - - - NOTE  - - - NOTE  - - - NOTE  - - - NOTE  - - - NOTE  - -

class RandomStall( Component ):
  def construct( s, Type, stall_prob=0, stall_seed=0xdeadbeef ):

    s.recv = RecvIfcRTL( Type )
    s.send = SendIfcRTL( Type )

    s.recv.msg //= s.send.msg

    stall_rgen = Random( stall_seed )

    s.rand_value = 0
    s.stall_prob = stall_prob

    @update_ff
    def up_rand():
      s.rand_value = stall_rgen.random()

    @update
    def up_stall_rdy():
      s.recv.rdy @= s.send.rdy & (s.rand_value > stall_prob)
    @update
    def up_stall_val():
      s.send.val @= s.recv.val & (s.rand_value > stall_prob)

  def line_trace( s ):
    return "[ ]" if s.rand_value > s.stall_prob else "[#]"

class InelasticDelayPipe( Component ):

  def construct( s, Type, delay=0 ):

    s.recv = RecvIfcRTL( Type )
    s.send = SendIfcRTL( Type )

    if delay == 0:
      s.recv //= s.send
    else:
      s.pipe = deque([None]*delay)

      # pipe behavior -- rdy goes through
      s.recv.rdy //= s.send.rdy

      @update_ff
      def up_delay():

        if s.send.val:
          if s.send.rdy:
            s.pipe[-1] = None
            s.pipe.rotate()
        else:
          s.pipe.rotate()

        if s.recv.rdy & s.recv.val:
          s.pipe[0] = clone_deepcopy( s.recv.msg )

        if s.pipe[-1] is None:
          s.send.val <<= 0
        else:
          s.send.val <<= 1
          s.send.msg <<= s.pipe[-1]

  def line_trace( s ):
    return f"{s.recv}>{s.send}"

class MagicMemoryRTL( Component ):

  # Magical methods

  def read_mem( s, addr, size ):
    return s.mem.read_mem( addr, size )

  def write_mem( s, addr, data ):
    return s.mem.write_mem( addr, data )

  # Actual stuff
  def construct( s, nports, mem_ifc_dtypes=[mk_mem_msg(8,32,32), mk_mem_msg(8,32,32)],
                    stall_prob=0, extra_latency=0, mem_nbytes=2**20 ):

    # Local constants

    assert len(mem_ifc_dtypes) == nports
    req_classes  = [ x for (x,y) in mem_ifc_dtypes ]
    resp_classes = [ y for (x,y) in mem_ifc_dtypes ]

    s.mem = MagicMemoryFL( mem_nbytes )

    # Interface

    s.ifc = [ MinionIfcRTL( req_classes[i], resp_classes[i] ) for i in range(nports) ]


    # stall and delays
    s.req_stalls = [ RandomStall( req_classes[i], stall_prob, i ) for i in range(nports) ]
    s.req_qs     = [ PipeQueueRTL( req_classes[i], 1 ) for i in range(nports) ]
    s.resp_qs    = [ InelasticDelayPipe( resp_classes[i], extra_latency ) for i in range(nports) ]

    for i in range(nports):
      s.req_stalls[i].recv //= s.ifc[i].req
      s.req_stalls[i].send //= s.req_qs[i].recv
      s.resp_qs[i].send    //= s.ifc[i].resp


    @update
    def up_mem():

      for i in range(nports):
        s.req_qs[i].send.rdy @= 0
        s.resp_qs[i].recv.val @= 0

        if s.req_qs[i].send.val & s.resp_qs[i].recv.rdy:

          # Dequeue memory request message

          req = s.req_qs[i].send.msg
          len_ = int(req.len)
          if len_ == 0: len_ = req_classes[i].data_nbits >> 3

          if   req.type_ == MemMsgType.READ:
            resp = resp_classes[i]( req.type_, req.opaque, 0, req.len,
                                    zext( s.mem.read( req.addr, len_ ), req_classes[i].data_nbits ) )

          elif  req.type_ == MemMsgType.WRITE:
            s.mem.write( req.addr, len_, req.data[0:len_<<3] )
            # FIXME do we really set len=0 in response when doing subword wr?
            # resp = resp_classes[i]( req.type_, req.opaque, 0, req.len, 0 )
            resp = resp_classes[i]( req.type_, req.opaque, 0, 0, 0 )

          elif  req.type_ == MemMsgType.AMO_ADD   or \
                req.type_ == MemMsgType.AMO_AND   or \
                req.type_ == MemMsgType.AMO_MAX   or \
                req.type_ == MemMsgType.AMO_MAXU  or \
                req.type_ == MemMsgType.AMO_MIN   or \
                req.type_ == MemMsgType.AMO_MINU  or \
                req.type_ == MemMsgType.AMO_OR    or \
                req.type_ == MemMsgType.AMO_SWAP  or \
                req.type_ == MemMsgType.AMO_XOR:
            resp = resp_classes[i]( req.type_, req.opaque, 0, req.len,
               s.mem.amo( req.type_, req.addr, len_, req.data ) )

          # Invalid type
          else:
            assert False

          s.req_qs[i].send.rdy @= 1
          s.resp_qs[i].recv.val @= 1
          s.resp_qs[i].recv.msg @= resp

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    return "|".join( f"{s.req_stalls[i].line_trace()}{s.ifc[i].req}>{s.ifc[i].resp}"
                        for i in range(len(s.ifc)) )
