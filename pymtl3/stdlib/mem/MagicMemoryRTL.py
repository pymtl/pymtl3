"""
========================================================================
MagicMemoryRTL
========================================================================
Magic memory with RTL interfaces.

Author : Shunning Jiang, Peitian Pan
Date   : Nov 16, 2020
"""

from pymtl3 import *

from .MagicMemoryCL import MagicMemoryCL
from .mem_ifcs import MemMinionIfcRTL, MemMasterIfcRTL
from .MemMsg import MemMsgType, mk_mem_msg

class MagicMemRTL2CLAdapter( Component ):

  def construct( s, ReqType, RespType ):

    s.minion = MemMinionIfcRTL( ReqType, RespType )
    s.master = MemMasterIfcRTL( ReqType, RespType )

    s.minion //= s.master

class MagicMemoryRTL( Component ):

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

    s.mem = MagicMemoryCL( nports, mem_ifc_dtypes, stall_prob, latency, mem_nbytes )
    s.adapters = [ MagicMemRTL2CLAdapter( req_classes[i], resp_classes[i] ) for i in range(nports) ]

    # Connections

    for i in range(nports):
      s.ifc[i] //= s.adapters[i].minion
      s.adapters[i].master //= s.mem.ifc[i]

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    return s.mem.line_trace()
