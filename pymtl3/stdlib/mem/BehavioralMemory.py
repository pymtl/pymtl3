from pymtl3 import *
from pymtl3.extra.pypy.fast_bytearray_funcs import (
    read_bytearray_bits,
    write_bytearray_bits,
)

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

class BehavioralMemory( Component ):

  def construct( s, mem_nbytes=1<<20 ):
    s.mem = bytearray( mem_nbytes )

    s.trace = "     "
    @update_once
    def up_clear_trace():
      s.trace = "     "

  def read( s, addr, nbytes ):
    assert len(s.mem) > (int(addr) + int(nbytes)), \
        f"Out-of-bound memory read of {int(nbytes)} bytes @ 0x{int(addr):#08x} detected at behavioral memory {s}!"
    s.trace = "[rd ]"
    return read_bytearray_bits( s.mem, addr, nbytes )

  def write( s, addr, nbytes, data ):
    assert isinstance(data, Bits), \
        f"Write operand {data} needs to be Bits to indicate write length!"
    assert len(s.mem) > (int(addr) + data.nbits // 8), \
        f"Out-of-bound memory write of {data.nbits//8} bytes @ 0x{int(addr):#08x} detected at behavioral memory {s}!"
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
    assert len(s.mem) > (int(addr) + int(size)), \
        f"Out-of-bound memory read of {int(size)} bytes @ 0x{int(addr):#08x} detected at behavioral memory {s}!"
    return s.mem[ addr : addr + size ]

  def write_mem( s, addr, data ):
    assert isinstance(data, (bytes, bytearray, list)), \
        f"Write operand {data} needs to be bytes, bytearray, or list of bytes!"
    assert len(s.mem) > (int(addr) + len(data)), \
        f"Out-of-bound memory write of {len(data)} bytes @ 0x{int(addr):#08x} detected at behavioral memory {s}!"
    s.mem[ addr : addr + len(data) ] = data

  def line_trace( s ):
    return s.trace
