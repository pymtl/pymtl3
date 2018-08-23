from pymtl import *
from pclib.ifcs import MemIfcRTL, MemIfcCL, MemIfcFL, MemReqMsg, MemRespMsg
from pclib.test import TestMemoryFL, TestMemoryCL
from pclib.update import Reg

class MemFillFL( MethodsAdapt ):
  def __init__( s, base_addr=0x1000, size=100 ):
    s.mem = MemIfcFL()

    s.finished = False

    @s.pausable_update
    def up_fill():

      if not s.finished:

        # Stream the writes

        for i in xrange(size):
          s.mem.write( base_addr+i*4, 4, i )

        # Check the answers

        for i in xrange(size):
          assert s.mem.read( base_addr+i*4, 4 ) == i
          print "#{} passed".format( i )

      s.finished = True

  def done( s ):
    return s.finished

  def line_trace( s ):
    return ""

class MemFillCL( MethodsAdapt ):

  def __init__( s, base_addr=0x1000, size=100 ):
    s.ReqType  = MemReqMsg(8,32,32)
    s.RespType = MemRespMsg(8,32)

    s.mem = MemIfcCL( (s.ReqType, s.RespType) )
    s.mem.resp.enq |= s.recv
    s.mem.resp.rdy |= s.recv_rdy

    s.i    = 0
    s.size = size

    @s.update
    def up_fill():
      if s.mem.req.rdy() and s.i < s.size:
        s.mem.req.enq( s.ReqType.mk_wr( s.i+100, base_addr+s.i*4, 4, s.i ) )
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

class MemFillRTL( MethodsAdapt ):

  def __init__( s, base_addr=0x1000, size=100 ):
    s.ReqType  = MemReqMsg(8,32,32)
    s.RespType = MemRespMsg(8,32)

    s.mem = MemIfcRTL( (s.ReqType, s.RespType) )

    s.state = Reg( Bits2 )

    s.STATE_IDLE = 0
    s.STATE_CALC = 1

    s.i    = Reg( Bits32 )
    s.size = Reg( Bits32 )
    s.fini = Reg( Bits1 )
    s.ts = 0

    @s.update
    def up_send():
      
      curr_state  = s.state.out

      s.state.in_ = s.state.out
      s.i.in_     = s.i.out
      s.size.in_  = s.size.out
      s.mem.resp.rdy = Bits1( 0 )

      if curr_state == s.STATE_IDLE:
        s.mem.req.en   = Bits1( 0 )
        s.mem.req.msg  = s.ReqType()

        s.i.in_    = Bits32( 0    )
        s.size.in_ = Bits32( size )

        if not s.fini.out:
          s.state.in_ = s.STATE_CALC

      elif curr_state == s.STATE_CALC:
        s.mem.resp.rdy = Bits1( 1 )
        s.mem.req.en   = Bits1( 0 )
        s.mem.req.msg  = s.ReqType()

        if s.mem.req.rdy:# and s.ts & 1:
          s.mem.req.en  = Bits1( 1 )
          s.mem.req.msg = s.ReqType.mk_wr( s.i.out+100, base_addr+s.i.out*4, 4, s.i.out )
          s.i.in_ = s.i.out + 1

        s.ts += 1

        if s.i.in_ == s.size.out:
          s.state.in_ = s.STATE_IDLE
          s.fini.in_  = Bits1( 1 )

  def done( s ):
    return s.fini.out

  def line_trace( s ):
    return "{}/{}".format( s.i.line_trace(), s.size.out )

class Harness( MethodsAdapt ):
  def __init__( s, level='fl', base_addr=0x1000, size=100, mem_level='fl' ):

    if mem_level == 'fl':
      s.mem = TestMemoryFL()

      if   level == 'fl' :
        s.fill = MemFillFL( base_addr, size )( mem = s.mem.ifc )
      else:
        if level == 'cl' :  s.fill = MemFillCL ( base_addr, size )
        else:               s.fill = MemFillRTL( base_addr, size )

        s.connect( s.fill.mem, s.mem.ifc )

    if mem_level == 'cl':
      s.mem = TestMemoryCL( 1, [ MemReqMsg(8,32,32) ], [ MemRespMsg(8,32) ] )

      if   level == 'cl' :
        s.fill = MemFillCL( base_addr, size )( mem = s.mem.ifcs[0] )
      else:
        if level == 'fl' :  s.fill = MemFillFL ( base_addr, size )
        else:               s.fill = MemFillRTL( base_addr, size )

        s.connect( s.fill.mem, s.mem.ifcs[0] )

  def done( s ):
    return s.fill.done()

  def line_trace( s ):
    return s.fill.line_trace() + " >>> " + s.mem.line_trace()

if __name__ == "__main__":

  for mem_level in [ "fl","cl" ]: 
    for fill_level in [ "fl", "cl", "rtl"]:
      print
      print "----- fill_{} + mem_{} -----".format(fill_level, mem_level)
      A = Harness( fill_level, 0x1000, 10, mem_level )
      A.elaborate()
      A.print_schedule()

      T = 0
      while not A.done():
        A.cycle()
        print T,":", A.line_trace()
        T += 1
