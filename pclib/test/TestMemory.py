from pymtl import *
from collections import deque
from pclib.ifcs import valrdy_to_str, ValRdyBundle, MemReqMsg, MemRespMsg

class TestMemory( Updates ):

  def __init__( s, nports = 1, reqs  = [ MemReqMsg(8,32,32) ], \
                               resps = [ MemRespMsg(8,32)   ],
                               mem_nbytes=2**20 ):

    assert len(reqs) == len(resps), "[TestMemory] Should provide the same number of types for req and resp."
    assert len(reqs) == nports,     "[TestMemory] The number of types in the lists doesn't match the provided number of ports."

    s.nports = nports
    s.reqs   = [ ValRdyBundle( reqs[i]  ) for i in xrange(nports) ]
    s.resps  = [ ValRdyBundle( resps[i] ) for i in xrange(nports) ]

    s.nbytes = [0] * nports
    for i in xrange(nports):
      x = reqs [i].data.nbits
      y = resps[i].data.nbits
      assert x & 7 == 0 and y & 7 == 0 and x == y

      s.nbytes[i] = x >> 3

    s.mem = bytearray( mem_nbytes )

    @s.update_on_edge
    def up_test_memory():

      mem = s.mem
      for i in xrange(nports):

        if s.resps[i].val:
          if s.resps[i].rdy:
            s.resps[i].val = Bits1( 0 )
          else:
            s.reqs [i].rdy = Bits1( 0 )
        else:
          s.reqs [i].rdy = Bits1( 1 )

        # not pending response or a handshake has just finished

        if not s.reqs[i].val:
          continue

        nbytes = s.nbytes[i] if not s.reqs[i].msg.len else s.reqs[i].msg.len
        nbits  = s.nbytes[i] << 3
        begin  = s.reqs[i].msg.addr
        end    = begin + nbytes

        if s.reqs[i].msg.type_ == MemReqMsg.TYPE_READ:

          s.resps[i].val = Bits1( 1 )
          x, y = 0, 0
          for j in xrange( begin, end ):
            x += mem[j] << y
            y += 8
          s.resps[i].msg.type_  = s.reqs[i].msg.type_
          s.resps[i].msg.data   = Bits( nbits, x )
          s.resps[i].msg.opaque = s.reqs[i].msg.opaque
          s.resps[i].msg.len    = s.reqs[i].msg.len

        elif s.reqs[i].msg.type_ == MemReqMsg.TYPE_WRITE:

          s.resps[i].val = Bits1( 1 )
          # Copy write data bits into bytearray

          x = int( s.reqs[i].msg.data )
          for j in xrange( begin, end ):
            mem[j] = x & 255
            x >>= 8
          s.resps[i].msg.type_  = s.reqs[i].msg.type_
          s.resps[i].msg.data   = Bits( nbits, 0 )
          s.resps[i].msg.opaque = s.reqs[i].msg.opaque
          # s.resps[i].msg.len    = s.reqs[i].msg.len # FIXME
          s.resps[i].msg.len = 0 # I don't why but old test memory does this


  def write_mem( s, addr, data ):
    assert len(s.mem) > (addr + len(data))
    s.mem[ addr : addr + len(data) ] = data

  def read_mem( s, addr, size ):
    assert len(s.mem) > (addr + size)
    return s.mem[ addr : addr + size ]

  def line_trace( s ):

    trace_str = ""
    for req, resp in zip( s.reqs, s.resps ):
      trace_str += "[{}->{}] ".format( req.line_trace(), resp.line_trace() )

    return trace_str
