
import timeit

from Bits_v2 import Bits as Bv2
from Bits_v3 import Bits as Bv3

def test_lshift_arith_v2():
  g = Bv2(32, 0)
  for i in xrange(10000000):
    a = Bv2(32, 12938676)
    b = Bv2(32, i & 127)
    c = a + b
    d = a << b
    c = d | (b ^ c)
    d = c << (b & Bv2(31, 7) )
    g += d

  return g

def test_lshift_arith_v3():
  g = Bv3(32, 0)
  for i in xrange(10000000):
    a = Bv3(32, 12938676)
    b = Bv3(32, i & 127)
    c = a + b
    d = a << b
    c = d | (b ^ c)
    d = c << (b & Bv3(31, 7) )
    g += d

  return g

# print "[lshift_arith] v3 avg time:",sum(timeit.repeat( test_lshift_arith_v3, repeat=5, number=10 ))/5
# print "[lshift_arith] v3", test_lshift_arith_v3()
# print

# print "[lshift_arith] v2 avg time:",sum(timeit.repeat( test_lshift_arith_v2, repeat=5, number=10 ))/5
# print "[lshift_arith] v2", test_lshift_arith_v2()
# print

def test_idx_v2():
  g = Bv2(32, 0)
  for i in xrange(10000000):
    a = Bv2(32, i)
    b = Bv2(32, i & 31)
    a[int(b)] = a[b] ^ 1 # pymtl v2 bits bug
    g += a[b]

  return g

def test_idx_v3():
  g = Bv3(32, 0)
  for i in xrange(10000000):
    a = Bv3(32, i)
    b = Bv3(32, i & 31)
    a[b] = a[b] ^ 1
    g += a[b]

  return g

print "[idx] v3 avg time:",sum(timeit.repeat( test_idx_v3, repeat=5, number=10 ))/5
print "[idx] v3", test_idx_v3()
print

print "[idx] v2 avg time:",sum(timeit.repeat( test_idx_v2, repeat=5, number=10 ))/5
print "[idx] v2", test_idx_v2()
print

def test_slice_v2():
  g = Bv2(32, 0)
  for i in xrange(10000000):
    a = Bv2(32, i)
    b = Bv2(32, i & 31)
    a[int(b)] = a[b] ^ 1 # pymtl v2 bits bug
    g += a[b]

  return g

def test_slice_v3():
  g = Bv3(32, 0)
  for i in xrange(10000000):
    a = Bv3(32, i)
    b = Bv3(32, i & 31)
    a[b] = a[b] ^ 1
    g += a[b]

  return g

print "[slice] v3 avg time:",sum(timeit.repeat( test_slice_v3, repeat=5, number=10 ))/5
print "[slice] v3", test_slice_v3()
print

print "[slice] v2 avg time:",sum(timeit.repeat( test_slice_v2, repeat=5, number=10 ))/5
print "[slice] v2", test_slice_v2()
print
