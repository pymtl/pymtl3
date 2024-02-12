"""
========================================================================
Encoder_test
========================================================================
Test for RTL priority encoder.

Author : Yanghui Ou
  Date : Apr 5, 2019
"""
from pymtl3 import *
from pymtl3.stdlib.test_utils import TestVectorSimulator

from ..encoders import Encoder


def run_test( model, test_vectors ):

  def tv_in( model, test_vector ):
    model.in_ @= test_vector[0]

  def tv_out( model, test_vector ):
    assert model.out == test_vector[1]

  sim = TestVectorSimulator( model, test_vectors, tv_in, tv_out )
  sim.run_test()

def test_encoder_5_directed():

  model = Encoder( 5, 3 )
  run_test( model, [
    # in       out
    [ 0b00000, 0  ],
    [ 0b00001, 0  ],
    [ 0b00010, 1  ],
    [ 0b00100, 2  ],
    [ 0b01100, 3  ],
    [ 0b10000, 4  ]
  ] )
