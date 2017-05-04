from pymtl import *
from collections import deque
from pclib.ifcs import MemReqMsg, MemRespMsg, EnqIfcCL

AMO_FUNS = { MemReqMsg.TYPE_AMO_ADD  : lambda m,a : m+a,
             MemReqMsg.TYPE_AMO_AND  : lambda m,a : m&a,
             MemReqMsg.TYPE_AMO_OR   : lambda m,a : m|a,
             MemReqMsg.TYPE_AMO_XCHG : lambda m,a : a,
             MemReqMsg.TYPE_AMO_MIN  : min,
           }

class TestMemoryFL( object ):
  def __init__( s, mem_nbytes=1<<20, word_nbytes=4 ):
    s.mem       = bytearray( mem_nbytes )
    s.word_type = mk_bits( word_nbytes<<3 )

  def read( s, addr, nbytes ):
    ret, shamt = 0, 0
    end = addr + nbytes
    for j in xrange( addr, end ):
      ret += s.mem[j] << shamt
      shamt += 8
    return s.word_type( ret )

  def write( s, addr, nbytes, data ):
    tmp = int(data)
    end = addr + nbytes
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

class TestMemoryCL( TestMemoryFL, MethodsConnection ):
  def __init__( s, nports = 1, reqs  = [ MemReqMsg(8,32,32) ], \
                               resps = [ MemRespMsg(8,32)   ],
                               mem_nbytes=1<<20, word_nbytes=4 ):
    TestMemoryFL.__init__( s, mem_nbytes, word_nbytes )

    s.send = [ EnqIfcCL( reqs[i]  ) for i in xrange(nports) ]
    s.recv = [ EnqIfcCL( resps[i] ) for i in xrange(nports) ]

    s.req   = [ None ] * nports

    # Currently, only <=2 ports
    if nports >= 1:
      s.recv[0].enq |= s.recv0
      s.recv[0].rdy |= s.recv_rdy0

    if nports >= 2:
      s.recv[1].enq |= s.recv1
      s.recv[1].rdy |= s.recv_rdy1

    @s.update
    def up_testmem():

      for i in xrange(nports):
        req = s.req[i]

        if s.send[i].rdy() and req:
          len = req.len if req.len else ( reqs[i].data.nbits >> 3 )

          if   req.type_ == MemReqMsg.TYPE_READ:
            resp = resps[i].mk_rd( req.opaque, len, s.read( req.addr, len ) )
          elif req.type_ == MemReqMsg.TYPE_WRITE:
            s.write( req.addr, len, req.data )
            resp = resps[i].mk_wr( req.opaque ) # AMOS
          else:
            ret  = s.amo( req.type_, req.addr, len, req.data )
            resp = resps[i].mk_msg( req.type_, req.opaque, 0, len, ret )

          s.send[i].enq( resp )
          s.req[i] = None

    for i in xrange(nports):
      s.add_constraints(
        U(up_testmem) < M(s.recv[i].enq), # pipe behavior, send < recv
        U(up_testmem) < M(s.recv[i].rdy),
      )

  def recv0( s, msg ): # recv req
    s.req[0]  = msg

  def recv_rdy0( s ): # recv req
    return not s.req[0]

  def recv1( s, msg ): # recv req
    s.req[1]  = msg

  def recv_rdy1( s ): # recv req
    return not s.req[1]

  def line_trace( s ):
    return " > "
