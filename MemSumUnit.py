from pymtl import *
from pclib.ifcs import MemIfcRTL, MemIfcCL, MemIfcFL, MemReqMsg, MemRespMsg, mk_mem_msg_type
from pclib.test import TestMemoryFL, TestMemoryCL
from pclib.update import Reg

class MemSumFL( MethodsAdapt ):
  def __init__( s, base_addr=0x1000, size=100 ):
    s.mem = MemIfcFL()

    s.finished = False
    s.result = 0

    @s.pausable_update
    def up_sum():

      if not s.finished:

        for i in xrange(size):
          s.result += s.mem.read( base_addr+i*4, 4 )

        s.finished = True

  def done( s ):
    return s.finished

  def line_trace( s ):
    return ""

class MemSumCL( MethodsAdapt ):

  def __init__( s, base_addr=0x1000, size=100 ):

    s.ReqType, s.RespType = mk_mem_msg_type(8,32,32)

    s.mem = MemIfcCL( (s.ReqType, s.RespType) )
    s.connect( s.mem.resp.enq, s.recv )
    s.connect( s.mem.resp.rdy, s.recv_rdy )

    s.i        = 0
    s.size     = size
    s.result   = 0
    s.num_recv = 0

    @s.update
    def up_sum():
      if s.mem.req.rdy() and s.i < size:
        s.mem.req.enq( s.ReqType( 'rd', s.i, base_addr+s.i*4, 4 ) )
        s.i += 1

  def recv( s, msg ):
    s.num_recv += 1
    s.result   += msg.data

  def recv_rdy( s ):
    return True

  def done( s ):
    return s.num_recv == s.size

  def line_trace( s ):
    return "Last req send: #%d | num of resp received: #%d" % (s.i, s.num_recv)

class MemSumRTL( MethodsAdapt ):

  def __init__( s, base_addr=0x1000, size=100 ):

    s.ReqType, s.RespType = mk_mem_msg_type(8,32,32)

    s.mem = MemIfcRTL( (s.ReqType, s.RespType) )

    s.i        = Reg( Bits32 )
    s.num_recv = Reg( Bits32 )
    s.size     = size
    s.result   = Reg( Bits32 )

    @s.update
    def up_send():

      s.mem.req.en   = Bits1( 0 )
      s.mem.req.msg  = s.ReqType()
      s.i.in_        = s.i.out

      if (s.i.in_ < size) & s.mem.req.rdy:
        s.mem.req.en  = Bits1( 1 )
        s.mem.req.msg = s.ReqType( 'rd', s.i.out, base_addr+s.i.out*4, 4 )
        s.i.in_       = s.i.out + 1

    @s.update
    def up_recv_rdy():
      s.mem.resp.rdy = Bits1( 1 )

    @s.update
    def up_recv():

      s.num_recv.in_ = s.num_recv.out
      s.result.in_   = s.result.out

      if s.mem.resp.en:
        s.num_recv.in_ = s.num_recv.out + 1
        s.result.in_   = s.result.out + s.mem.resp.msg.data

  def done( s ):
    return s.num_recv.out == s.size

  def line_trace( s ):
    return "{}/{}".format( s.i.line_trace(), s.size )

class Harness( MethodsAdapt ):
  def __init__( s, level='fl', base_addr=0x1000, size=100, mem_level='fl' ):

    if mem_level == 'fl':
      s.mem = TestMemoryFL()

      if   level == 'fl' :
        s.memsum = MemSumFL( base_addr, size )( mem = s.mem.ifc )
      else:
        if level == 'cl' :  s.memsum = MemSumCL ( base_addr, size )
        else:               s.memsum = MemSumRTL( base_addr, size )

        s.connect( s.memsum.mem, s.mem.ifc )

    if mem_level == 'cl':
      s.mem = TestMemoryCL( 1, [ MemReqMsg(8,32,32) ], [ MemRespMsg(8,32) ] )

      if   level == 'cl' :
        s.memsum = MemSumCL( base_addr, size )( mem = s.mem.ifcs[0] )
      else:
        if level == 'fl' :  s.memsum = MemSumFL ( base_addr, size )
        else:               s.memsum = MemSumRTL( base_addr, size )

        s.connect( s.memsum.mem, s.mem.ifcs[0] )

    # dump data into mem, took from SortXcelFL

    import struct
    data = [ i*2 for i in xrange(size) ]
    data_bytes = struct.pack("<{}I".format(len(data)),*data)
    s.mem.write_mem( base_addr, data_bytes )

  def done( s ):
    return s.memsum.done()

  def line_trace( s ):
    return s.memsum.line_trace() + " >>> " + s.mem.line_trace()

if __name__ == "__main__":

  for mem_level in [ "fl","cl" ]: 
    for memsum_level in [ "fl", "cl", "rtl"]:
  # for mem_level in [ "fl" ]: 
    # for memsum_level in [ "rtl" ]:
      print
      print "----- sum_{} + mem_{} -----".format(memsum_level, mem_level)
      A = Harness( memsum_level, 0x1000, 10, mem_level )
      A.elaborate()
      # A.print_schedule()

      T = 0
      while not A.done():
        A.cycle()
        print T,":", A.line_trace()
        T += 1

      print "result = ", int(A.memsum.result)
