"""
========================================================================
bits_benchmark.py
========================================================================
Micro-benchmarking Python bits in PyMTL vs Python bits in Mamba

Author : Shunning Jiang
Date   : Dec 18, 2017
"""
from __future__ import absolute_import, division, print_function

import timeit

from Bits_gen import *
from Bits_v2 import Bits as Bv2
from Bits_v3 import Bits as Bv3
from six.moves import range

#=========================================================================
# ARITH
#=========================================================================

def ubmark_arith_v2():
  g = Bv2(32, 0)
  for i in range(10000000):
    a = Bv2(32, 12938676)
    b = Bv2(32, i & 127)
    c = a >> b
    d = a + b
    c = d | (b ^ c)
    d = c + (b & Bv2(31, 7) )
    g += d

  return g

def ubmark_arith_v3():
  g = Bv3(32, 0)
  for i in range(10000000):
    a = Bv3(32, 12938676)
    b = Bv3(32, i & 127)
    c = a >> b
    d = a + b
    c = d | (b ^ c)
    d = c + (b & Bv3(31, 7) )
    g += d

  return g

def ubmark_arith_fix():
  g = Bits32(0)
  for i in range(10000000):
    a = Bits32(12938676)
    b = Bits32(i & 127)
    c = a >> b
    d = a + b
    c = d | (b ^ c)
    d = c + (b & Bits31(7) )
    g += d

  return g

def ubmark_arith_int():
  g = 0
  for i in range(10000000):
    a = 12938676
    b = i & 127
    c = a >> b
    d = a + b
    c = d | (b ^ c)
    d = c + (b & 7)
    g += d

  return g

#=========================================================================
# LSHIFT
#=========================================================================

def ubmark_lshift_v2():
  g = Bv2(32, 0)
  for i in range(10000000):
    a = Bv2(32, 12938676)
    b = Bv2(32, i & 255)
    g += (a << b)

  return g

def ubmark_lshift_v3():
  g = Bv3(32, 0)
  for i in range(10000000):
    a = Bv3(32, 12938676)
    b = Bv3(32, i & 255)
    g += (a << b)

  return g

def ubmark_lshift_fix():
  g = Bits32(0)
  for i in range(10000000):
    a = Bits32(12938676)
    b = Bits32(i & 255)
    g += (a << b)

  return g

def ubmark_lshift_int():
  g = 0
  for i in range(10000000):
    a = 12938676
    b = i & 255
    if b < 32:
      g = (g+(a << b)) & ((1<<32)-1)
    else:
      g += 0

  return g

#=========================================================================
# IDX
#=========================================================================

def ubmark_idx_fix():
  g = Bits32(0)
  for i in range(10000000):
    a = Bits32(i)
    b = Bits32(i & 31)
    a[b] = a[b] ^ 1
    g += a[b]

  return g

def ubmark_idx_v2():
  g = Bv2(32, 0)
  for i in range(10000000):
    a = Bv2(32, i)
    b = Bv2(32, i & 31)
    a[int(b)] = a[b] ^ 1 # pymtl v2 bits bug
    g += a[b]

  return g

def ubmark_idx_v3():
  g = Bv3(32, 0)
  for i in range(10000000):
    a = Bv3(32, i)
    b = Bv3(32, i & 31)
    a[b] = a[b] ^ 1
    g += a[b]

  return g

#=========================================================================
# SLICE
#=========================================================================

def ubmark_slice_fix():
  g = Bits32(0)
  for i in range(10000000):
    a = Bits32(i)
    b = Bits6(i & 15)
    c = Bits6(32 - (i & 7))
    a[b:c] = a[b:c] ^ 2147483647
    g += a[b:c]

  return g

def ubmark_slice_v2():
  g = Bv2(32, 0)
  for i in range(10000000):
    a = Bv2(32, i)
    b = Bv2(6, i & 15)
    c = Bv2(6, 32 - (i & 7) )
    a[int(b):int(c)] = a[int(b):int(c)] ^ 2147483647
    g += a[int(b):int(c)]

  return g

def ubmark_slice_v3():
  g = Bv3(32, 0)
  for i in range(10000000):
    a = Bv3(32, i)
    b = Bv3(6, i & 15)
    c = Bv3(6, 32 - (i & 7))
    a[b:c] = a[b:c] ^ 2147483647
    g += a[b:c]

  return g

print("[arith] int  ", hex(ubmark_arith_int()))
print("[arith] int   avg time:",sum(timeit.repeat( ubmark_arith_int, repeat=5, number=10 ))/5)
print()
print("[arith] Bits*", ubmark_arith_fix())
print("[arith] Bits* avg time:",sum(timeit.repeat( ubmark_arith_fix, repeat=5, number=10 ))/5)
print()
print("[arith] v3   ", ubmark_arith_v3())
print("[arith] v3    avg time:",sum(timeit.repeat( ubmark_arith_v3, repeat=5, number=10 ))/5)
print()
print("[arith] v2   ", ubmark_arith_v2())
print("[arith] v2    avg time:",sum(timeit.repeat( ubmark_arith_v2, repeat=5, number=10 ))/5)
print()
print("[lshift] int  ", hex(ubmark_lshift_int()))
print("[lshift] int   avg time:",sum(timeit.repeat( ubmark_lshift_int, repeat=5, number=10 ))/5)
print()
print("[lshift] Bits*", ubmark_lshift_fix())
print("[lshift] Bits* avg time:",sum(timeit.repeat( ubmark_lshift_fix, repeat=5, number=10 ))/5)
print()
print("[lshift] v3   ", ubmark_lshift_v3())
print("[lshift] v3    avg time:",sum(timeit.repeat( ubmark_lshift_v3, repeat=5, number=10 ))/5)
print()
print("[lshift] v2   ", ubmark_lshift_v2())
print("[lshift] v2    avg time:",sum(timeit.repeat( ubmark_lshift_v2, repeat=5, number=10 ))/5)
print()
print("[idx] Bits*", ubmark_idx_fix())
print("[idx] Bits* avg time:",sum(timeit.repeat( ubmark_idx_fix, repeat=5, number=10 ))/5)
print()
print("[idx] v3   ", ubmark_idx_v3())
print("[idx] v3    avg time:",sum(timeit.repeat( ubmark_idx_v3, repeat=5, number=10 ))/5)
print()
print("[idx] v2   ", ubmark_idx_v2())
print("[idx] v2    avg time:",sum(timeit.repeat( ubmark_idx_v2, repeat=5, number=10 ))/5)
print()
print("[slice] Bits*", ubmark_slice_fix())
print("[slice] Bits* avg time:",sum(timeit.repeat( ubmark_slice_fix, repeat=5, number=10 ))/5)
print()
print("[slice] v3   ", ubmark_slice_v3())
print("[slice] v3    avg time:",sum(timeit.repeat( ubmark_slice_v3, repeat=5, number=10 ))/5)
print()
print("[slice] v2   ", ubmark_slice_v2())
print("[slice] v2    avg time:",sum(timeit.repeat( ubmark_slice_v2, repeat=5, number=10 ))/5)
print()
