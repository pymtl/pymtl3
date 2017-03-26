
import timeit

from Bits_v2 import Bits as Bv2
from Bits_v3 import Bits as Bv3

def ubmark_arith_v2():
  g = Bv2(32, 0)
  for i in xrange(10000000):
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
  for i in xrange(10000000):
    a = Bv3(32, 12938676)
    b = Bv3(32, i & 127)
    c = a >> b
    d = a + b
    c = d | (b ^ c)
    d = c + (b & Bv3(31, 7) )
    g += d

  return g

print "[arith] v3 avg time:",sum(timeit.repeat( ubmark_arith_v3, repeat=5, number=10 ))/5
print "[arith] v3", ubmark_arith_v3()

print "[arith] v2 avg time:",sum(timeit.repeat( ubmark_arith_v2, repeat=5, number=10 ))/5
print "[arith] v2", ubmark_arith_v2()
print

def ubmark_lshift_v2():
  g = Bv2(32, 0)
  for i in xrange(10000000):
    a = Bv2(32, 12938676)
    b = Bv2(32, i & 255)
    g += (a << b)

  return g

def ubmark_lshift_v3():
  g = Bv3(32, 0)
  for i in xrange(10000000):
    a = Bv3(32, 12938676)
    b = Bv3(32, i & 255)
    g += (a << b)

  return g

print "[lshift] v3 avg time:",sum(timeit.repeat( ubmark_lshift_v3, repeat=5, number=10 ))/5
print "[lshift] v3", ubmark_lshift_v3()

print "[lshift] v2 avg time:",sum(timeit.repeat( ubmark_lshift_v2, repeat=5, number=10 ))/5
print "[lshift] v2", ubmark_lshift_v2()
print

def ubmark_idx_v2():
  g = Bv2(32, 0)
  for i in xrange(10000000):
    a = Bv2(32, i)
    b = Bv2(32, i & 31)
    a[int(b)] = a[b] ^ 1 # pymtl v2 bits bug
    g += a[b]

  return g

def ubmark_idx_v3():
  g = Bv3(32, 0)
  for i in xrange(10000000):
    a = Bv3(32, i)
    b = Bv3(32, i & 31)
    a[b] = a[b] ^ 1
    g += a[b]

  return g

print "[idx] v3 avg time:",sum(timeit.repeat( ubmark_idx_v3, repeat=5, number=10 ))/5
print "[idx] v3", ubmark_idx_v3()

print "[idx] v2 avg time:",sum(timeit.repeat( ubmark_idx_v2, repeat=5, number=10 ))/5
print "[idx] v2", ubmark_idx_v2()
print

def ubmark_slice_v2():
  g = Bv2(32, 0)
  for i in xrange(10000000):
    a = Bv2(32, i)
    b = Bv2(6, i & 15)
    c = Bv2(6, 32 - (i & 7) )
    a[int(b):int(c)] = a[int(b):int(c)] ^ 2147483647
    g += a[int(b):int(c)]

  return g

def ubmark_slice_v3():
  g = Bv3(32, 0)
  for i in xrange(10000000):
    a = Bv3(32, i)
    b = Bv3(6, i & 15)
    c = Bv3(6, 32 - (i & 7))
    a[b:c] = a[b:c] ^ 2147483647
    g += a[b:c]

  return g

print "[slice] v3 avg time:",sum(timeit.repeat( ubmark_slice_v3, repeat=5, number=10 ))/5
print "[slice] v3", ubmark_slice_v3()

print "[slice] v2 avg time:",sum(timeit.repeat( ubmark_slice_v2, repeat=5, number=10 ))/5
print "[slice] v2", ubmark_slice_v2()
print
