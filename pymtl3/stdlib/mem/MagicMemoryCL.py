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

from pymtl3 import *
from pymtl3.stdlib.delays import DelayPipeDeqCL, DelayPipeSendCL, StallCL

from .MagicMemoryFL import MagicMemoryFL
from .mem_ifcs import MemMinionIfcCL
from .MemMsg import MemMsgType, mk_mem_msg

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

class MagicMemoryCL( Component ):

  # Magical methods

  def read_mem( s, addr, size ):
    return s.mem.read_mem( addr, size )

  def write_mem( s, addr, data ):
    return s.mem.write_mem( addr, data )

  # Actual stuff
  def construct( s, nports, mem_ifc_dtypes=[mk_mem_msg(8,32,32), mk_mem_msg(8,32,32)], stall_prob=0, latency=1, mem_nbytes=2**20 ):

    # Local constants

    nports = 2

    s.nports = nports
    # req_classes  = [ x for (x,y) in mem_ifc_dtypes ]
    # resp_classes = [ y for (x,y) in mem_ifc_dtypes ]

    req_classes  = [ Bits78, Bits78 ]
    resp_classes = [ Bits48, Bits48 ]

    s.mem = MagicMemoryFL( mem_nbytes )

    # Interface

    s.ifc = [ MemMinionIfcCL( req_classes[i], resp_classes[i] ) for i in range(nports) ]

    # Queues
    req_latency = min(1, latency)
    resp_latency = latency - req_latency

    s.req_stalls = [ StallCL( stall_prob, i )     for i in range(nports) ]
    s.req_qs  = [ DelayPipeDeqCL( req_latency )   for i in range(nports) ]
    s.resp_qs = [ DelayPipeSendCL( resp_latency ) for i in range(nports) ]

    for i in range(nports):
      s.req_stalls[i].recv //= s.ifc[i].req
      s.resp_qs[i].send    //= s.ifc[i].resp

      s.req_qs[i].enq      //= s.req_stalls[i].send

    @update_once
    def up_mem():

      for i in range(s.nports):

        if s.req_qs[i].deq.rdy() and s.resp_qs[i].enq.rdy():

          # Dequeue memory request message

          req = s.req_qs[i].deq()
          len_ = int(req[32:34])
          if len_ == 0: len_ = 4

          #
          # READ
          #
          if   req[74:78] == MemMsgType.READ:
            resp = resp_classes[i](0)
            resp[44:48] = req[74:78]
            resp[36:44] = req[66:74]
            resp[34:36] = Bits2(0)
            resp[32:34] = req[32:34]
            resp[0:32]  = s.mem.read(req[34:66], len_)

          #
          # WRITE
          #
          elif  req[74:78] == MemMsgType.WRITE:
            s.mem.write( req[34:66], len_, req[0:32] )
            # FIXME do we really set len=0 in response when doing subword wr?
            # resp = resp_classes[i]( req.type_, req.opaque, 0, req.len, 0 )
            # resp = resp_classes[i]( req.type_, req.opaque, 0, 0, 0 )
            resp = resp_classes[i](0)
            resp[44:48] = req[74:78]
            resp[36:44] = req[66:74]
            resp[34:36] = Bits2(0)
            resp[32:34] = Bits2(0)
            resp[0:32]  = Bits32(0)

          #
          # AMOs
          #
          elif      req[74:78] == MemMsgType.AMO_ADD   or \
                req[74:78] == MemMsgType.AMO_AND   or \
                req[74:78] == MemMsgType.AMO_MAX   or \
                req[74:78] == MemMsgType.AMO_MAXU  or \
                req[74:78] == MemMsgType.AMO_MIN   or \
                req[74:78] == MemMsgType.AMO_MINU  or \
                req[74:78] == MemMsgType.AMO_OR    or \
                req[74:78] == MemMsgType.AMO_SWAP  or \
                req[74:78] == MemMsgType.AMO_XOR:
            # resp = resp_classes[i]( req.type_, req.opaque, 0, req.len,
            #    s.mem.amo( req.type_, req.addr, len_, req.data ) )
            resp = resp_classes[i](0)
            resp[44:48] = req[74:78]
            resp[36:44] = req[66:74]
            resp[34:36] = Bits2(0)
            resp[32:34] = Bits2(req[32:34])
            resp[0:32]  = Bits32(s.mem.amo(req[74:78], req[34:66], len_, req[0:32]))


          # INV
          elif  req[74:78] == MemMsgType.INV:
            resp = resp_classes[i]( req[74:78], req[66:74], 0, 0, 0 )

          # FLUSH
          elif  req[74:78] == MemMsgType.FLUSH:
            resp = resp_classes[i]( req[74:78], req[66:74], 0, 0, 0 )

          # Invalid type
          else:
            assert( False )

          s.resp_qs[i].enq( resp )

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    msg = ""
    for i in range( s.nports ):
      msg += f"[{i}] {str(s.ifc[i].req)} {str(s.ifc[i].resp)} "
    return msg
