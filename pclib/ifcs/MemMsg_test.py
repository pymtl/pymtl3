#=========================================================================
# MemMsg_test
#=========================================================================
# Test suite for the memory messages

from pymtl  import *
from MemMsg import mk_mem_msg

#-------------------------------------------------------------------------
# test_req_fields
#-------------------------------------------------------------------------

def test_req_fields():

  # Create msg

  req_type, resp_type = mk_mem_msg(8,16,40)

  msg = req_type( req_type.TYPE_READ, 7, 0x1000, 3 )

  # Verify msg

  assert msg.type_  == 0
  assert msg.opaque == 7
  assert msg.addr   == 0x1000
  assert msg.len    == 3

  # Create msg

  msg = req_type( req_type.TYPE_WRITE, 9, 0x2000, 0, 0xdeadbeef )

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

  req_type, resp_type = mk_mem_msg(8,16,40)

  # Create msg

  msg = req_type( req_type.TYPE_READ, 7, 0x1000, 3, 0 )

  # Verify string

  assert str(msg) == "rd:07:1000:          "

  req_type, resp_type = mk_mem_msg(4,16,40)

  # Create msg

  msg = req_type( req_type.TYPE_WRITE, 9, 0x2000, 4, 0xdeadbeef )

  # Verify string

  assert str(msg) == "wr:9:2000:00deadbeef"

#-------------------------------------------------------------------------
# test_resp_fields
#-------------------------------------------------------------------------

def test_resp_fields():

  req_type, resp_type = mk_mem_msg(8,16,40)

  # Create msg

  msg = resp_type( resp_type.TYPE_READ, 7, 2, 3, 0x0000adbeef )

  # Verify msg

  assert msg.type_  == 0
  assert msg.opaque == 7
  assert msg.test   == 2
  assert msg.len    == 3
  assert msg.data   == 0x0000adbeef

  # Create msg

  msg = resp_type( resp_type.TYPE_WRITE, 9, 1, 0, 0 )

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

  req_type, resp_type = mk_mem_msg(8,16,40)

  # Create msg

  msg = resp_type( resp_type.TYPE_READ, 7, 2, 3, 0x0000adbeef )

  # Verify string

  assert str(msg) == "rd:07:2:0000adbeef"

  req_type, resp_type = mk_mem_msg(4,16,40)

  # Create msg

  msg = resp_type( resp_type.TYPE_WRITE, 9, 1, 0, 0 )

  # Verify string

  assert str(msg) == "wr:9:1:          "

