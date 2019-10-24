"""
======================================================================
Crossbar_test.py
======================================================================
"""
from pymtl3 import *
from pymtl3.stdlib.test import TestVectorSimulator

from .Crossbar import Crossbar


#-----------------------------------------------------------------------
# run_test_crossbar
#-----------------------------------------------------------------------
def run_test_crossbar( cls, args, test_vectors ):

  model = cls( *args )

  n, T = args
  Tsel = mk_bits( clog2( n ) )

  # Define functions mapping the test vector to ports in model

  def tv_in( model, test_vector ):
    n = len( model.in_ )

    for i in range(n):
      model.in_[i] = T(test_vector[i])
      model.sel[i] = Tsel(test_vector[n+i])

  def tv_out( model, test_vector ):
    n = len( model.in_ )

    for i in range(n):
      assert model.out[i] == T(test_vector[n*2+i])

  # Run the test

  sim = TestVectorSimulator( model, test_vectors, tv_in, tv_out )
  sim.run_test()

#-----------------------------------------------------------------------
# test_crossbar3
#-----------------------------------------------------------------------

def test_crossbar3():
  model = Crossbar( 3, Bits16 )
  run_test_crossbar( Crossbar, (3, Bits16), [
    [ 0xdead, 0xbeef, 0xcafe, 0, 1, 2, 0xdead, 0xbeef, 0xcafe ],
    [ 0xdead, 0xbeef, 0xcafe, 0, 2, 1, 0xdead, 0xcafe, 0xbeef ],
    [ 0xdead, 0xbeef, 0xcafe, 1, 2, 0, 0xbeef, 0xcafe, 0xdead ],
    [ 0xdead, 0xbeef, 0xcafe, 1, 0, 2, 0xbeef, 0xdead, 0xcafe ],
    [ 0xdead, 0xbeef, 0xcafe, 2, 1, 0, 0xcafe, 0xbeef, 0xdead ],
    [ 0xdead, 0xbeef, 0xcafe, 2, 0, 1, 0xcafe, 0xdead, 0xbeef ],
  ])
