from pymtl3 import *
from pymtl3.extra.pypy.fast_bytearray_funcs import (
    read_bytearray_bits,
    write_bytearray_bits,
)

from .mem_ifcs import MemMinionIfcFL
from .MemMsg import MemMsgType

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

class MagicMemoryFL( Component ):

  def construct( s, mem_nbytes=1<<20 ):
    s.mem = bytearray( mem_nbytes )

    s.ifc = MemMinionIfcFL( s.read, s.write, s.amo )

    s.trace = "     "
    @update_once
    def up_clear_trace():
      s.trace = "     "

  def read( s, addr, nbytes ):
    s.trace = "[rd ]"
    return read_bytearray_bits( s.mem, addr, nbytes )

  def write( s, addr, nbytes, data ):
    s.trace = "[wr ]"
    write_bytearray_bits( s.mem, addr, nbytes, data )

    # addr = int(addr)
    # end  = addr + nbytes

    # while addr < end:
      # s.mem[addr] = data & 255
      # data >>= 8
      # addr += 1
    # s.trace = "[wr ]"

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
