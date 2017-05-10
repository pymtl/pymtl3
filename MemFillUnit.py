from pymtl import *
from pclib.ifcs import MemIfcCL, MemIfcFL, MemReqMsg, MemRespMsg
from pclib.test import TestMemoryFL

class MemFillFL( MethodsAdapt ):
  def __init__( s, base_addr=0x1000, size=100 ):
    s.memifc = MemIfcFL()

    s.finished = False

    @s.update
    def up_fill():

      # Stream the writes

      for i in xrange(size):
        s.memifc.write( base_addr+((i&131071)<<2), 4, i&131071)

      # Check the answers

      for i in xrange(size):
        assert s.memifc.read( base_addr+((i&131071)<<2), 4 ) == i&131071
        print "#{} passed".format( i )

      s.finished = True

  def done( s ):
    return s.finished

  def line_trace( s ):
    return ""

class MemFillCL( MethodsAdapt ):

  def __init__( s, base_addr=0x1000, size=100 ):
    s.req_type  = MemReqMsg(32,32,32) # 32 bit opaque
    s.resp_type = MemRespMsg(32,32)   # 32 bit opaque

    s.memifc = MemIfcCL( (s.req_type, s.resp_type) )
    s.memifc.resp.enq |= s.recv
    s.memifc.resp.rdy |= s.recv_rdy

    s.i    = 0
    s.size = size

    @s.update
    def up_fill():
      if s.memifc.req.rdy() and s.i < s.size:
        s.memifc.req.enq( s.req_type.mk_wr( s.i+100, base_addr+(s.i<<2), 4, s.i ) )
        s.i += 1

    s.last_recv = -1

  def recv( s, msg ):
    s.last_recv = msg.opaque

  def recv_rdy( s ):
    return True

  def done( s ):
    return s.last_recv == s.size + 100 -1

  def line_trace( s ):
    return "Last req send: #%d | Last resp recv: #%d" % (s.i, s.last_recv)

class Harness( MethodsAdapt ):
  def __init__( s, level='fl', base_addr=0x1000, size=100 ):

    s.mem = TestMemoryFL()

    if   level == 'fl' :
      s.fill = MemFillFL( base_addr, size )( memifc = s.mem.ifc )
    else:
      if level == 'cl' :  s.fill = MemFillCL ( base_addr, size )
      else:               s.fill = MemFillRTL( base_addr, size )

      s.connect( s.fill.memifc, s.mem.ifc )

  def done( s ):
    return s.fill.done()

  def line_trace( s ):
    return s.fill.line_trace()

if __name__ == "__main__":

  # for level in [ "fl", "cl", "rtl"]:
  for level in [ "cl" ]:
    A = Harness( level, base_addr = 0x100, size = 100000 )
    A.elaborate()
    A.print_schedule()

    T = 0
    while not A.done():
      A.cycle()
      # print T,":", A.line_trace()
      T += 1
