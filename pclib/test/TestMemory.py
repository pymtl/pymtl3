from pymtl import *
from collections import deque
from pclib.ifcs import MemReqMsg, MemRespMsg, EnqIfcCL, MemIfcFL, MemIfcCL
from pclib.cl   import ValidEntry

AMO_FUNS = { MemReqMsg.TYPE_AMO_ADD  : lambda m,a : m+a,
             MemReqMsg.TYPE_AMO_AND  : lambda m,a : m&a,
             MemReqMsg.TYPE_AMO_OR   : lambda m,a : m|a,
             MemReqMsg.TYPE_AMO_XCHG : lambda m,a : a,
             MemReqMsg.TYPE_AMO_MIN  : min,
           }

class TestMemoryFL( MethodsAdapt ):
  def __init__( s, mem_nbytes=1<<20 ):
    s.mem       = bytearray( mem_nbytes )
    s.ifc       = MemIfcFL()
    s.ifc.read  |= s.read
    s.ifc.write |= s.write
    s.ifc.amo   |= s.amo

  def read( s, addr, nbytes ):
    ret, shamt = 0, 0
    addr = int(addr)
    end  = addr + int(nbytes)
    for j in xrange( addr, end ):
      ret += s.mem[j] << shamt
      shamt += 8
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

  def line_trace( s ):
    return ""

class TestMemoryCL( MethodsAdapt ):
  def __init__( s, nports = 1, reqs  = [ MemReqMsg(8,32,32) ], \
                               resps = [ MemRespMsg(8,32)   ],
                               mem_nbytes=1<<20 ):
    s.mem = TestMemoryFL( mem_nbytes )

    s.ifcs = [ MemIfcCL( (reqs[i], resps[i]) ) for i in xrange(nports) ]

    s.reqs  = reqs
    s.resps = resps
    s.req   = [ ValidEntry( False, None ) ] * nports
    s.resp  = [ ValidEntry( False, None ) ] * nports # for line trace

    s.nports = nports

    # Currently, only <=2 ports
    if nports >= 1:
      s.ifcs[0].req.enq |= s.recv0
      s.ifcs[0].req.rdy |= s.recv_rdy0

    if nports >= 2:
      s.ifcs[1].req.enq |= s.recv1
      s.ifcs[1].req.rdy |= s.recv_rdy1

    @s.update
    def up_testmem():

      for i in xrange(nports):
        req = s.req[i]
        s.resp[i] = ValidEntry( False, None )

        if s.ifcs[i].resp.rdy() and req.val:
          req = req.msg
          len = req.len if req.len else ( reqs[i].data.nbits >> 3 )

          if   req.type_ == MemReqMsg.TYPE_READ:
            resp = resps[i].mk_rd( req.opaque, len, s.mem.read( req.addr, len ) )

          elif req.type_ == MemReqMsg.TYPE_WRITE:
            s.mem.write( req.addr, len, req.data )
            resp = resps[i].mk_wr( req.opaque )

          else: # AMOS
            resp = resps[i].mk_msg( req.type_, req.opaque, 0, len, \
                              s.mem.amo( req.type_, req.addr, len, req.data ))

          s.ifcs[i].resp.enq( resp )
          s.req[i]  = ValidEntry( False, None ) # clear pending req
          s.resp[i] = ValidEntry( True, resp ) # for line trace

    for i in xrange(nports):
      s.add_constraints(
        U(up_testmem) < M(s.ifcs[i].req.enq), # pipe behavior, send < recv
        U(up_testmem) < M(s.ifcs[i].req.rdy),
      )

  def recv0( s, msg ): # recv req
    s.req[0] = ValidEntry( val=True, msg=msg )

  def recv_rdy0( s ): # recv req
    return not s.req[0].val

  def recv1( s, msg ): # recv req
    s.req[1] = ValidEntry( val=True, msg=msg )

  def recv_rdy1( s ): # recv req
    return not s.req[1].val

  def read_mem( s, addr, size ):
    return s.mem.read_mem( addr, size )

  def write_mem( s, addr, data ):
    return s.mem.write_mem( addr, data )

  def line_trace( s ):
    return "|".join( [ "{}>{}".format( s.req[i].msg  if s.req[i].val  else "".ljust(len(str(s.reqs[i]()))),
                                   s.resp[i].msg if s.resp[i].val else "".ljust(len(str(s.resps[i]()))) ) \
                                for i in xrange(s.nports) ] )
