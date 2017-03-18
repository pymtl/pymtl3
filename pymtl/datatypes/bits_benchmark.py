
from Bits_v2 import Bits as Bv2
from Bits_v3 import Bits as Bv3

def test_v2():
  a = Bv2(32, 12938676)
  b = Bv2(32, 96818)
  c = a + b
  d = a << c
  c = d | (b ^ c)
  d = c << (b & Bv2(32, 7) )
  return d

def test_v3():
  a = Bv3(32, 12938676)
  b = Bv3(32, 96818)
  c = a + b
  d = a << c
  c = d | (b ^ c)
  d = c << (b & Bv3(32, 7) )
  return d

print "v2",test_v2()
print "v3",hex(test_v3())

import timeit

print timeit.repeat( test_v2, number = 10000 )
print timeit.repeat( test_v3, number = 10000 )
