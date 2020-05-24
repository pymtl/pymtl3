"""
========================================================================
XcelMsg_test
========================================================================

Author : Yanghui Ou
  Date : June 3, 2019
"""
from pymtl3 import *

from ..XcelMsg import XcelMsgType, mk_xcel_msg, mk_xcel_req_msg, mk_xcel_resp_msg

#-------------------------------------------------------------------------
# test_req_fields
#-------------------------------------------------------------------------

def test_req_fields():

  # Create msg

  ReqType = mk_xcel_req_msg( 4, 32 )

  msg = ReqType( XcelMsgType.READ, 1, 0x1000 )

  # Verify msg

  assert msg.type_ == 0
  assert msg.addr  == 1
  assert msg.data  == 0x1000

  # Create msg

  msg = ReqType( XcelMsgType.WRITE, 10, 0xdeadbeef )

  # Verify msg

  assert msg.type_ == 1
  assert msg.addr  == 10
  assert msg.data  == 0xdeadbeef

#-------------------------------------------------------------------------
# test_req_str
#-------------------------------------------------------------------------

def test_req_str():

  ReqType = mk_xcel_req_msg( 4, 32 )

  # Create msg

  msg = ReqType( XcelMsgType.READ, 7, 0x1000 )

  # Verify string

  assert str(msg) == "rd:7:        "

  ReqType = mk_xcel_req_msg( 4, 32 )

  # Create msg

  msg = ReqType( XcelMsgType.WRITE, 9, 0x2000 )

  # Verify string

  assert str(msg) == "wr:9:00002000"

#-------------------------------------------------------------------------
# test_resp_fields
#-------------------------------------------------------------------------

def test_resp_fields():

  RespType = mk_xcel_resp_msg( 40 )

  # Create msg

  msg = RespType( XcelMsgType.READ, 0xf000adbeef )

  # Verify msg

  assert msg.type_  == 0
  assert msg.data   == 0xf000adbeef

  # Create msg

  msg = RespType( XcelMsgType.WRITE, 0 )

  # Verify msg

  assert msg.type_  == 1
  assert msg.data   == 0

#-------------------------------------------------------------------------
# test_resp_str
#-------------------------------------------------------------------------

def test_resp_str():

  RespType = mk_xcel_resp_msg( 40 )

  # Create msg

  msg = RespType( XcelMsgType.READ, 0x000badbeef )

  # Verify string

  assert str(msg) == "rd:000badbeef"

  RespType = mk_xcel_resp_msg( 40 )

  # Create msg

  msg = RespType( XcelMsgType.WRITE, 0 )

  # Verify string

  assert str(msg) == "wr:          "
