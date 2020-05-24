"""
========================================================================
MemMsg_test
========================================================================

Author : Shunning Jiang
Date   : Mar 10, 2018
"""
from pymtl3 import *

from ..MemMsg import MemMsgType, mk_mem_msg, mk_mem_req_msg, mk_mem_resp_msg

#-------------------------------------------------------------------------
# test_req_fields
#-------------------------------------------------------------------------

def test_req_fields():

  # Create msg

  ReqType = mk_mem_req_msg(8,16,40)

  msg = ReqType( MemMsgType.READ, 7, 0x1000, 3, 0 )

  # Verify msg

  assert msg.type_  == 0
  assert msg.opaque == 7
  assert msg.addr   == 0x1000
  assert msg.len    == 3

  # Create msg

  msg = ReqType( MemMsgType.WRITE, 9, 0x2000, 0, 0xdeadbeef )

  # Verify msg

  assert msg.type_  == 1
  assert msg.opaque == 9
  assert msg.addr   == 0x2000
  assert msg.len    == 0
  assert msg.data   == 0xdeadbeef

#-------------------------------------------------------------------------
# test_req_str
#-------------------------------------------------------------------------

def test_req_str():

  ReqType = mk_mem_req_msg(8,16,40)

  # Create msg

  msg = ReqType( MemMsgType.READ, 7, 0x1000, 3, 0 )

  # Verify string

  assert str(msg) == "rd:07:1000:3:          "

  ReqType = mk_mem_req_msg(4,16,40)

  # Create msg

  msg = ReqType( MemMsgType.WRITE, 9, 0x2000, 4, 0xdeadbeef )

  # Verify string

  assert str(msg) == "wr:9:2000:4:00deadbeef"

#-------------------------------------------------------------------------
# test_resp_fields
#-------------------------------------------------------------------------

def test_resp_fields():

  RespType = mk_mem_resp_msg(8,40)

  # Create msg

  msg = RespType( MemMsgType.READ, 7, 2, 3, 0xf000adbeef )

  # Verify msg

  assert msg.type_  == 0
  assert msg.opaque == 7
  assert msg.test   == 2
  assert msg.len    == 3
  assert msg.data   == 0xf000adbeef

  # Create msg

  msg = RespType( MemMsgType.WRITE, 9, 1, 0, 0 )

  # Verify msg

  assert msg.type_  == 1
  assert msg.opaque == 9
  assert msg.test   == 1
  assert msg.len    == 0
  assert msg.data   == 0

#-------------------------------------------------------------------------
# test_resp_str
#-------------------------------------------------------------------------

def test_resp_str():

  RespType = mk_mem_resp_msg(8,40)

  # Create msg

  msg = RespType( MemMsgType.READ, 7, 2, 3, 0x0000adbeef )

  # Verify string

  assert str(msg) == "rd:07:2:3:0000adbeef"

  RespType = mk_mem_resp_msg(4,40)

  # Create msg

  msg = RespType( MemMsgType.WRITE, 9, 1, 0, 0 )

  # Verify string

  assert str(msg) == "wr:9:1:0:          "
