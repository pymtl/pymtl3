#=========================================================================
# MagicMemoryO3RTL.py
#=========================================================================
# Magic memory with out-of-order memory responses.
#
# Author : Peitian Pan
# Date   : Dec 3, 2020

from pymtl3 import *

from .MagicMemoryRTL import MagicMemoryRTL
from ..queues.RandomDelayQueue import RandomDelayQueue
from .mem_ifcs import MemMinionIfcRTL
from .MemMsg import mk_mem_msg

class MagicMemoryO3RTL( Component ):

  # Magical methods

  def read_mem( s, addr, size ):
    return s.mem.read_mem( addr, size )

  def write_mem( s, addr, data ):
    return s.mem.write_mem( addr, data )

  # Actual stuff
  def construct( s, nports, mem_ifc_dtypes=[mk_mem_msg(8,32,32), mk_mem_msg(8,32,32)], stall_prob=0, latency=1, mem_nbytes=2**20 ):

    # Local constants

    s.nports = nports
    req_classes  = [ x for (x,y) in mem_ifc_dtypes ]
    resp_classes = [ y for (x,y) in mem_ifc_dtypes ]

    # Interface

    s.ifc = [ MemMinionIfcRTL( req_classes[i], resp_classes[i] ) for i in range(nports) ]

    # Components

    s.mem = MagicMemoryRTL( nports, mem_ifc_dtypes, stall_prob, latency, mem_nbytes )

    s.delay_q = [ RandomDelayQueue( resp_classes[i], 0 ) for i in range(s.nports) ]

    # Connections

    for i in range(nports):
      s.ifc[i].req //= s.mem.ifc[i].req
      s.mem.ifc[i].resp //= s.delay_q[i].enq
      s.ifc[i].resp.en //= lambda: s.delay_q[i].deq.rdy & s.ifc[i].resp.rdy
      s.delay_q[i].deq.en //= s.ifc[i].resp.en
      s.ifc[i].resp.msg //= s.delay_q[i].deq.ret

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    return s.mem.line_trace()
