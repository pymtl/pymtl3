"""
========================================================================
MemMsg.py
========================================================================
New memory message type implementation.

Author : Shunning Jiang, Yanghui Ou
Date   : Mar 12, 2018
"""
from pymtl3 import *


class MemMsgType:
  READ       = 0
  WRITE      = 1
  # write no-refill
  WRITE_INIT = 2
  AMO_ADD    = 3
  AMO_AND    = 4
  AMO_OR     = 5
  AMO_SWAP   = 6
  AMO_MIN    = 7
  AMO_MINU   = 8
  AMO_MAX    = 9
  AMO_MAXU   = 10
  AMO_XOR    = 11
  LR         = 12 # Load-Reserved
  SC         = 13 # Store-Conditional
  INV        = 14 # Cache invalidation
  FLUSH      = 15 # Cache flush

  str = {
    READ       : "rd",
    WRITE      : "wr",
    WRITE_INIT : "in",
    AMO_ADD    : "ad",
    AMO_AND    : "an",
    AMO_OR     : "or",
    AMO_SWAP   : "sw",
    AMO_MIN    : "mi",
    AMO_MINU   : "mu",
    AMO_MAX    : "mx",
    AMO_MAXU   : "xu",
    AMO_XOR    : "xo",
    LR         : "lr",
    SC         : "sc",
    INV        : "iv",
    FLUSH      : "fl"
  }

def mk_mem_msg( opq, addr, data ):
  return mk_mem_req_msg( opq, addr, data ), mk_mem_resp_msg( opq, data )

def mk_mem_req_msg( o, a, d ):

  @bitstruct
  class MemReqMsg:
    type_  : Bits4
    opaque : mk_bits( o           )
    addr   : mk_bits( a           )
    len    : mk_bits( clog2(d>>3) )
    data   : mk_bits( d           )

    data_nbits = d

    def __str__( self ):
      return "{}:{}:{}:{}:{}".format(
        MemMsgType.str[ int( self.type_ ) ],
        self.opaque,
        self.addr,
        self.len,
        self.data if self.type_ != MemMsgType.READ else " " * ( d//4 ),
      )

  return MemReqMsg

def mk_mem_resp_msg( o, d ):

  @bitstruct
  class MemRespMsg:
    type_  : Bits4
    opaque : mk_bits( o           )
    test   : Bits2
    len    : mk_bits( clog2(d>>3) )
    data   : mk_bits( d           )

    data_nbits = d

    def __str__( self ):
      return "{}:{}:{}:{}:{}".format(
        MemMsgType.str[ int( self.type_ ) ],
        self.opaque,
        self.test,
        self.len,
        self.data if self.type_ != MemMsgType.WRITE else " " * ( d//4 ),
      )
  return MemRespMsg
