from __future__ import absolute_import, division, print_function

from pclib.ifcs import MemMsgType
from pclib.ifcs.mem_ifcs import MemMinionIfcFL
from pymtl import *

AMO_FUNS = { MemMsgType.AMO_ADD  : lambda m,a : m+a,
             MemMsgType.AMO_AND  : lambda m,a : m&a,
             MemMsgType.AMO_OR   : lambda m,a : m|a,
             MemMsgType.AMO_SWAP : lambda m,a : a,
             MemMsgType.AMO_MIN  : lambda m,a : m if m.int() < a.int() else a,
             MemMsgType.AMO_MINU : min,
             MemMsgType.AMO_MAX  : lambda m,a : m if m.int() > a.int() else a,
             MemMsgType.AMO_MAXU : max,
             MemMsgType.AMO_XOR  : lambda m,a : m^a,
           }

class MemoryFL( Component ):

  def construct( s, mem_nbytes=1<<20 ):
    s.mem = bytearray( mem_nbytes )

    s.ifc = MemMinionIfcFL( s.read, s.write, s.amo )

    s.trace = "     "
    @s.update
    def up_clear_trace():
      s.trace = "     "

  def read( s, addr, nbytes ):
    nbytes = int(nbytes)
    nbits = nbytes << 3
    ret, shamt = Bits( nbits, 0 ), Bits( nbits, 0 )
    addr = int(addr)
    end  = addr + nbytes
    for j in xrange( addr, end ):
      ret += Bits( nbits, s.mem[j] ) << shamt
      shamt += Bits4(8)
    s.trace = "[rd ]"
    return ret

  def write( s, addr, nbytes, data ):
    tmp  = int(data)
    addr = int(addr)
    end  = addr + int(nbytes)
    for j in xrange( addr, end ):
      s.mem[j] = tmp & 255
      tmp >>= 8
    s.trace = "[wr ]"

  def amo( s, amo, addr, nbytes, data ):
    ret = s.read( addr, nbytes )
    s.write( addr, nbytes, AMO_FUNS[ int(amo) ]( ret, data ) )
    s.trace = "[amo]"
    return ret

  def read_mem( s, addr, size ):
    assert len(s.mem) > (addr + size)
    return s.mem[ addr : addr + size ]

  def write_mem( s, addr, data ):
    assert len(s.mem) > (addr + len(data))
    s.mem[ addr : addr + len(data) ] = data

  def line_trace( s ):
    return s.trace
