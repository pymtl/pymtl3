from pymtl import *
from collections import deque
from pclib.ifcs import MemReqMsg, MemRespMsg
from pclib.ifcs import InValRdyIfc, OutValRdyIfc
from valrdy_queues import PipeQueue1RTL

AMO_FUNS = { MemReqMsg.TYPE_AMO_ADD  : lambda m,a : m+a,
             MemReqMsg.TYPE_AMO_AND  : lambda m,a : m&a,
             MemReqMsg.TYPE_AMO_OR   : lambda m,a : m|a,
             MemReqMsg.TYPE_AMO_XCHG : lambda m,a : a,
             MemReqMsg.TYPE_AMO_MIN  : min,
           }

class TestMemory( object ):
  def __init__( s, mem_nbytes=1<<20 ):
    s.mem       = bytearray( mem_nbytes )

  def read( s, addr, nbytes ):
    nbytes = int(nbytes)
    ret, shamt = Bits( nbytes<<3, 0 ), Bits32(0)
    addr = int(addr)
    end  = addr + nbytes
    for j in xrange( addr, end ):
      ret += Bits32( s.mem[j] ) << shamt
      shamt += Bits32(8)
    return ret

  def write( s, addr, nbytes, data ):
    tmp  = int(data)
    addr = int(addr)
    end  = addr + int(nbytes)
    for j in xrange( addr, end ):
      s.mem[j] = tmp & 255
      tmp >>= 8

  def amo( s, amo, addr, nbytes, data ):
    ret = s.read( addr, nbytes )
    s.write( addr, nbytes, AMO_FUNS[ int(amo) ]( ret, data ) )
    return ret

  def read_mem( s, addr, size ):
    assert len(s.mem) > (addr + size)
    return s.mem[ addr : addr + size ]

  def write_mem( s, addr, data ):
    assert len(s.mem) > (addr + len(data))
    s.mem[ addr : addr + len(data) ] = data

  def __getitem__( s, idx ):
    return s.mem[ idx ]

  def __setitem__( s, idx, data ):
    s.mem[ idx ] = data

class TestMemoryRTL( RTLComponent ):
  def __init__( s, nports = 1, req_types = [ MemReqMsg(8,32,32) ], \
                               resp_types = [ MemRespMsg(8,32)   ],
                               mem_nbytes=1<<20 ):
    s.mem = TestMemory( mem_nbytes )

    s.reqs  = [ InValRdyIfc( req_types[i] ) for i in xrange(nports) ]
    s.resps = [ OutValRdyIfc( resp_types[i] ) for i in xrange(nports) ]
    s.resp_qs = [ PipeQueue1RTL( resp_types[i] ) for i in xrange(nports) ]

    for i in xrange(nports):
      s.connect( s.resps[i], s.resp_qs[i].deq )

    s.req_types  = req_types
    s.resp_types = resp_types

    s.nports = nports

    @s.update
    def up_set_rdy():
      for i in xrange(nports):
        s.reqs[i].rdy = s.resp_qs[i].enq.rdy

    @s.update
    def up_process_memreq():

      for i in xrange(nports):
        s.resp_qs[i].enq.val = Bits1( 0 )

        if s.reqs[i].val & s.resp_qs[i].enq.rdy:
          req = s.reqs[i].msg
          len = req.len if req.len else ( s.reqs[i].msg.data.nbits >> 3 )

          if   req.type_ == MemReqMsg.TYPE_READ:
            resp = s.resp_types[i].mk_rd( req.opaque, len, s.mem.read( req.addr, len ) )

          elif req.type_ == MemReqMsg.TYPE_WRITE:
            s.mem.write( req.addr, len, req.data )
            resp = s.resp_types[i].mk_wr( req.opaque )

          else: # AMOS
            resp = s.resp_types[i].mk_msg( req.type_, req.opaque, 0, len, \
                                            s.mem.amo( req.type_, req.addr, len, req.data ))

          s.resp_qs[i].enq.val = Bits1( 1 )
          s.resp_qs[i].enq.msg = resp

  def read_mem( s, addr, size ):
    return s.mem.read_mem( addr, size )

  def write_mem( s, addr, data ):
    return s.mem.write_mem( addr, data )

  def line_trace( s ):
    return "|".join( [ "{}>{}".format( s.reqs[i].line_trace(), s.resps[i].line_trace() ) \
                                for i in xrange(s.nports) ] )
