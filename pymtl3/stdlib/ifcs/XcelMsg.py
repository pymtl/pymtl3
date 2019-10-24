"""
========================================================================
XcelMsg.py
========================================================================
Accelerator message type implementation.

Author : Yanghui Ou
Date   : June 3, 2019
"""
from pymtl3 import *


def mk_xcel_msg( addr, data ):
  return mk_xcel_req_msg( addr, data ), mk_xcel_resp_msg( data )

def mk_xcel_req_msg( addr, data ):
  AddrType = mk_bits( addr )
  DataType = mk_bits( data )
  cls_name = "XcelReqMsg_{}_{}".format( addr, data )

  def req_to_str( self ):
    return "{}:{}:{}".format(
      "rd" if self.type_ == XcelMsgType.READ else "wr",
      AddrType( self.addr ),
      DataType( self.data ) if self.type_ != XcelMsgType.READ else
      " " * ( data//4 ),
    )

  req_cls = mk_bitstruct( cls_name, {
    'type_': Bits1,
    'addr':  AddrType,
    'data':  DataType,
  },
  namespace = {
    '__str__' : req_to_str
  })
  return req_cls

def mk_xcel_resp_msg( data ):
  DataType = mk_bits( data )
  cls_name = "XcelRespMsg_{}".format( data )

  def resp_to_str( self ):
    return "{}:{}".format(
      "rd" if self.type_ == XcelMsgType.READ else "wr",
      DataType( self.data ) if self.type_ != XcelMsgType.WRITE else
      " " * ( data//4 ),
    )

  resp_cls = mk_bitstruct( cls_name, {
    'type_': Bits1,
    'data':  DataType,
  },
  namespace = {
    '__str__' : resp_to_str
  })
  return resp_cls

class XcelMsgType:
  # TODO: figure out whether we want to use Bits1 here.
  READ  = Bits1(0)
  WRITE = Bits1(1)
