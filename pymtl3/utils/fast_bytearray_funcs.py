#=========================================================================
# fast_bytearray_funcs.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Feb 25, 2020

try:
  from mamba import read_bytearray_bits
except:
  from pymtl3.datatypes import Bits

  def read_bytearray_bits( arr, addr, nbytes ):
    ret = 0
    begin = int(addr)
    addr  = begin + nbytes - 1

    while addr >= begin:
      ret = (ret << 8) + arr[addr]
      addr -= 1

    return Bits( nbytes << 3, ret )

try:
  from mamba import write_bytearray_bits
except:
  from pymtl3.datatypes import Bits

  def write_bytearray_bits( arr, addr, nbytes, data ):
    addr = int(addr)
    end  = addr + nbytes

    while addr < end:
      arr[addr] = data & 255
      data >>= 8
      addr += 1
