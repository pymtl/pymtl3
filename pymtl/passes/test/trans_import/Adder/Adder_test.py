from pymtl import *
from pymtl.passes.test.trans_import.Verify import Verify

test_vector = [
      'in0    in1         reset', 
      [ 0,      1,            1], 
      [ 2,      4,            1], 
      [ 32,     64,           1], 
      [ 100,    200,          1], 
      [ 1000,   2048,         1],
    ]

def test_Adder_32( ):

  verify( 'Adder', test_vector, Bits32 ) 

def test_Adder_16( ):

  verify( 'Adder', test_vector, Bits16 )

def test_Adder_8( ):

  verify( 'Adder', test_vector, Bits8 )

if __name__ == '__main__':
  test_Adder_32()
  test_Adder_8()
