"""
========================================================================
XcelMsg.py
========================================================================
Accelerator message type implementation.

Author : Yanghui Ou
Date   : June 3, 2019
"""
from pymtl3 import *


class XcelMsgType:
  # TODO: figure out whether we want to use Bits1 here.
  READ  = 0
  WRITE = 1

  str = {
    READ  : "rd",
    WRITE : "wr",
  }

def mk_xcel_msg( addr, data ):
  return mk_xcel_req_msg( addr, data ), mk_xcel_resp_msg( data )

def mk_xcel_req_msg( a, d ):
  @bitstruct
  class XcelReqMsg:
    type_ : Bits1
    addr  : mk_bits( a )
    data  : mk_bits( d )

    def __str__( self ):
      return "{}:{}:{}".format(
        XcelMsgType.str[ int(self.type_) ],
        self.addr,
        self.data if self.type_ != XcelMsgType.READ else " " * ( d//4 ),
      )

  return XcelReqMsg

def mk_xcel_resp_msg( d ):
  @bitstruct
  class XcelRespMsg:
    type_ : Bits1
    data  : mk_bits( d )

    def __str__( self ):
      return "{}:{}".format(
        XcelMsgType.str[ int(self.type_) ],
        self.data if self.type_ != XcelMsgType.WRITE else " " * ( d//4 ),
      )

  return XcelRespMsg
