#=========================================================================
# MemMsg_test
#=========================================================================
# Test suite for the memory messages

from pymtl  import *
from MemMsg import MemReqMsg, MemRespMsg

#-------------------------------------------------------------------------
# test_req_fields
#-------------------------------------------------------------------------

def test_req_fields():

  # Create msg

  msg = MemReqMsg(8,16,40).mk_rd( 7, 0x1000, 3 )

  # Verify msg

  assert msg.type_  == 0
  assert msg.opaque == 7
  assert msg.addr   == 0x1000
  assert msg.len    == 3

  # Create msg

  msg = MemReqMsg(4,16,40).mk_wr( 9, 0x2000, 4, 0xdeadbeef )

  # Verify msg

  assert msg.type_  == 1
  assert msg.opaque == 9
  assert msg.addr   == 0x2000
  assert msg.len    == 4
  assert msg.data   == 0xdeadbeef

#-------------------------------------------------------------------------
# test_req_str
#-------------------------------------------------------------------------

def test_req_str():

  # Create msg

  msg = MemReqMsg(8,16,40).mk_msg( MemReqMsg.TYPE_READ, 7, 0x1000, 3, 0 )

  # Verify string

  assert str(msg) == "rd:07:1000:          "

  # Create msg

  msg = MemReqMsg(4,16,40).mk_msg( MemReqMsg.TYPE_WRITE, 9, 0x2000, 4, 0xdeadbeef )

  # Verify string

  assert str(msg) == "wr:9:2000:00deadbeef"

#-------------------------------------------------------------------------
# test_resp_fields
#-------------------------------------------------------------------------

def test_resp_fields():

  # Create msg

  msg = MemRespMsg(8,40).mk_msg( MemRespMsg.TYPE_READ, 7, 2, 3, 0x0000adbeef )

  # Verify msg

  assert msg.type_  == 0
  assert msg.opaque == 7
  assert msg.test   == 2
  assert msg.len    == 3
  assert msg.data   == 0x0000adbeef

  # Create msg

  msg = MemRespMsg(4,40).mk_msg( MemRespMsg.TYPE_WRITE, 9, 1, 0, 0 )

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

  # Create msg

  msg = MemRespMsg(8,40).mk_msg( MemRespMsg.TYPE_READ, 7, 2, 3, 0x0000adbeef )

  # Verify string

  assert str(msg) == "rd:07:2:0000adbeef"

  # Create msg

  msg = MemRespMsg(4,40).mk_msg( MemRespMsg.TYPE_WRITE, 9, 1, 0, 0 )

  # Verify string

  assert str(msg) == "wr:9:1:          "

