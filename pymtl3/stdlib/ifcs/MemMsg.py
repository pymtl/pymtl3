"""
========================================================================
MemMsg.py
========================================================================
New memory message type implementation.

Author : Shunning Jiang, Yanghui Ou
Date   : Mar 12, 2018
"""
from pymtl3 import *


def mk_mem_msg( opq, addr, data ):
  return mk_mem_req_msg( opq, addr, data ), mk_mem_resp_msg( opq, data )

def mk_mem_req_msg( opq, addr, data ):
  OpqType  = mk_bits( opq            )
  AddrType = mk_bits( addr           )
  LenType  = mk_bits( clog2(data>>3) )
  DataType = mk_bits( data           )
  cls_name = "MemReqMsg_{}_{}_{}".format( opq, addr, data )

  def req_to_str( self ):
    return "{}:{}:{}:{}:{}".format(
      MemMsgType.str[ int( self.type_ ) ],
      OpqType( self.opaque ),
      AddrType( self.addr ),
      LenType( self.len ),
      DataType( self.data ) if self.type_ != MemMsgType.READ else
      " " * ( data//4 ),
    )

  req_cls = mk_bitstruct( cls_name, {
    'type_':  Bits4,
    'opaque': OpqType,
    'addr':   AddrType,
    'len':    LenType,
    'data':   DataType,
  },
  namespace = {
    '__str__' : req_to_str
  })

  req_cls.data_nbits = data
  return req_cls

def mk_mem_resp_msg( opq, data ):
  OpqType  = mk_bits( opq            )
  LenType  = mk_bits( clog2(data>>3) )
  DataType = mk_bits( data           )
  cls_name = "MemRespMsg_{}_{}".format( opq, data )

  def resp_to_str( self ):
    return "{}:{}:{}:{}:{}".format(
      MemMsgType.str[ int( self.type_ ) ],
      OpqType( self.opaque ),
      Bits2( self.test ),
      LenType( self.len ),
      DataType( self.data ) if self.type_ != MemMsgType.WRITE else
      " " * ( data//4 ),
    )

  resp_cls = mk_bitstruct( cls_name, {
    'type_':  Bits4,
    'opaque': OpqType,
    'test':   Bits2,
    'len':    LenType,
    'data':   DataType,
  },
  namespace = {
    '__str__' : resp_to_str
  })

  resp_cls.data_nbits = data
  return resp_cls

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
  }
