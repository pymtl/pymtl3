"""
=============================================================================
arbiters_test.py
=============================================================================
This file contains unit tests for the arbiters collection models.
"""
from pymtl3 import *
from pymtl3.stdlib.test_utils import TestVectorSimulator

from ..arbiters import RoundRobinArbiter, RoundRobinArbiterEn


def run_test( model, tvs ):

  # Define functions mapping the test vector to ports in model

  def tv_in( model, tv ):
    model.reqs @= tv[0]

  def tv_out( model, tv ):
    assert model.grants == tv[1]

  # Run the test

  sim = TestVectorSimulator( model, tvs, tv_in, tv_out )

  sim.run_test()

#------------------------------------------------------------------------------
# test_rr_arb_4
#------------------------------------------------------------------------------
# RoundRobinArbiter with four requesters
def test_rr_arb_4():

  run_test( RoundRobinArbiter(4), [

    # reqs     grants
    [ 0b0000,  0b0000 ],

    [ 0b0001,  0b0001 ],
    [ 0b0010,  0b0010 ],
    [ 0b0100,  0b0100 ],
    [ 0b1000,  0b1000 ],

    [ 0b1111,  0b0001 ],
    [ 0b1111,  0b0010 ],
    [ 0b1111,  0b0100 ],
    [ 0b1111,  0b1000 ],
    [ 0b1111,  0b0001 ],

    [ 0b1100,  0b0100 ],
    [ 0b1010,  0b1000 ],
    [ 0b1001,  0b0001 ],
    [ 0b0110,  0b0010 ],
    [ 0b0101,  0b0100 ],
    [ 0b0011,  0b0001 ],

    [ 0b1110,  0b0010 ],
    [ 0b1101,  0b0100 ],
    [ 0b1011,  0b1000 ],
    [ 0b0111,  0b0001 ],

  ])

#------------------------------------------------------------------------------
# run_en_test
#------------------------------------------------------------------------------
# Test driver for RoundRobinArbiterEn
def run_en_test( model, tvs ):

  # Define functions mapping the test vector to ports in model

  def tv_in( model, tv ):
    model.en   @= tv[0]
    model.reqs @= tv[1]

  def tv_out( model, tv ):
    assert model.grants == tv[2]

  # Run the test

  sim = TestVectorSimulator( model, tvs, tv_in, tv_out )
  sim.run_test()

#------------------------------------------------------------------------------
# test_rr_arb_en_4
#------------------------------------------------------------------------------
# RoundRobinArbiterEn with four requesters
def test_rr_arb_en_4( cmdline_opts ):

  run_en_test( RoundRobinArbiterEn(4), [

    # reqs     grants
    [ 0, 0b0000,  0b0000 ],
    [ 1, 0b0000,  0b0000 ],

    [ 1, 0b0001,  0b0001 ],
    [ 0, 0b0010,  0b0010 ],
    [ 1, 0b0010,  0b0010 ],
    [ 1, 0b0100,  0b0100 ],
    [ 0, 0b1000,  0b1000 ],
    [ 1, 0b1000,  0b1000 ],

    [ 1, 0b1111,  0b0001 ],
    [ 0, 0b1111,  0b0010 ],
    [ 0, 0b1111,  0b0010 ],
    [ 1, 0b1111,  0b0010 ],
    [ 1, 0b1111,  0b0100 ],
    [ 1, 0b1111,  0b1000 ],
    [ 0, 0b1111,  0b0001 ],
    [ 1, 0b1111,  0b0001 ],

    [ 0, 0b1100,  0b0100 ],
    [ 1, 0b1100,  0b0100 ],
    [ 0, 0b1010,  0b1000 ],
    [ 1, 0b1010,  0b1000 ],
    [ 1, 0b1001,  0b0001 ],
    [ 1, 0b0110,  0b0010 ],
    [ 1, 0b0101,  0b0100 ],
    [ 1, 0b0011,  0b0001 ],

    [ 1, 0b1110,  0b0010 ],
    [ 0, 0b1101,  0b0100 ],
    [ 1, 0b1101,  0b0100 ],
    [ 1, 0b1011,  0b1000 ],
    [ 0, 0b0111,  0b0001 ],
    [ 1, 0b0111,  0b0001 ],

  ])
