#========================================================================
# Adder_test.py
#========================================================================
# Testing the translation and import pass with an adder implementation.

from pymtl import *
from pymtl.passes.test.trans_import.Verify import Verify

test_vector = [
  'in0    in1   reset', 
  [ 0,    1,        1], 
  [ 2,    4,        1], 
  [ 32,   64,       1], 
  [ 100,  200,      1], 
  [ 1000, 2048,     1],
]

def test_Adder_32( ):
  Verify( 'Adder', test_vector, 'normal', Bits32 ) 

def test_Adder_16( ):
  Verify( 'Adder', test_vector, 'normal', Bits16 )
