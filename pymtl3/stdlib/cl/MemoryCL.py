"""
========================================================================
TestMemory
========================================================================
A behavioral Test Memory which is parameterized based on the number of
memory request/response ports. This version is a little different from
the one in pclib because we actually use the memory messages correctly
in the interface.

Author : Shunning Jiang
Date   : Mar 12, 2018
"""

from pymtl3 import *
from pymtl3.stdlib.fl import MemoryFL
from pymtl3.stdlib.ifcs import MemMsgType, mk_mem_msg
from pymtl3.stdlib.ifcs.mem_ifcs import MemMinionIfcCL

from .DelayPipeCL import DelayPipeDeqCL, DelayPipeSendCL

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

class MemoryCL( Component ):

  # Magical methods

  def read_mem( s, addr, size ):
    return s.mem.read_mem( addr, size )

  def write_mem( s, addr, data ):
    return s.mem.write_mem( addr, data )

  # Actual stuff
  def construct( s, nports, mem_ifc_dtypes=[mk_mem_msg(8,32,32), mk_mem_msg(8,32,32)], latency=1, mem_nbytes=2**20 ):

    # Local constants

    s.nports = nports
    req_classes  = [ x for (x,y) in mem_ifc_dtypes ]
    resp_classes = [ y for (x,y) in mem_ifc_dtypes ]

    s.mem = MemoryFL( mem_nbytes )

    # Interface

    s.ifc = [ MemMinionIfcCL( req_classes[i], resp_classes[i] ) for i in range(nports) ]

    # Queues
    req_latency = min(1, latency)
    resp_latency = latency - req_latency

    s.req_qs  = [ DelayPipeDeqCL( req_latency )( enq = s.ifc[i].req ) for i in range(nports) ]
    s.resp_qs = [ DelayPipeSendCL( resp_latency )( send = s.ifc[i].resp ) for i in range(nports) ]

    @s.update
    def up_mem():

      for i in range(s.nports):

        if s.req_qs[i].deq.rdy() and s.resp_qs[i].enq.rdy():

          # Dequeue memory request message

          req = s.req_qs[i].deq()
          len_ = int(req.len)
          if not len_: len_ = req_classes[i].data_nbits >> 3

          if   req.type_ == MemMsgType.READ:
            resp = resp_classes[i]( req.type_, req.opaque, 0, req.len,
                                           s.mem.read( req.addr, len_ ) )

          elif req.type_ == MemMsgType.WRITE:
            s.mem.write( req.addr, len_, req.data )
            # FIXME do we really set len=0 in response when doing subword wr?
            # resp = resp_classes[i]( req.type_, req.opaque, 0, req.len, 0 )
            resp = resp_classes[i]( req.type_, req.opaque, 0, 0, 0 )

          else: # AMOS
            resp = resp_classes[i]( req.type_, req.opaque, 0, req.len,
               s.mem.amo( req.type_, req.addr, len_, req.data ) )

          s.resp_qs[i].enq( resp )

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------
  # TODO: better line trace.

  def line_trace( s ):
    return "|".join( [ x[0].line_trace() + x[1].line_trace() for x in zip(s.req_qs, s.resp_qs) ] )
