from __future__ import absolute_import

from builtins import range

from pclib.test import TestVectorSimulator
from pymtl import *

from .Crossbar import Crossbar

# =======================================================================
# Crossbar_test.py
# =======================================================================


# -----------------------------------------------------------------------
# run_test_crossbar
# -----------------------------------------------------------------------
def run_test_crossbar(model, test_vectors):

    # Define functions mapping the test vector to ports in model

    def tv_in(model, test_vector):
        n = len(model.in_)

        for i in range(n):
            model.in_[i] = test_vector[i]
            model.sel[i] = test_vector[n + i]

    def tv_out(model, test_vector):
        n = len(model.in_)

        for i in range(n):
            assert model.out[i] == test_vector[n * 2 + i]

    # Run the test

    sim = TestVectorSimulator(model, test_vectors, tv_in, tv_out)
    sim.run_test()


# -----------------------------------------------------------------------
# test_crossbar3
# -----------------------------------------------------------------------


def test_crossbar3():
    model = Crossbar(3, Bits16)
    run_test_crossbar(
        model,
        [
            [0xDEAD, 0xBEEF, 0xCAFE, 0, 1, 2, 0xDEAD, 0xBEEF, 0xCAFE],
            [0xDEAD, 0xBEEF, 0xCAFE, 0, 2, 1, 0xDEAD, 0xCAFE, 0xBEEF],
            [0xDEAD, 0xBEEF, 0xCAFE, 1, 2, 0, 0xBEEF, 0xCAFE, 0xDEAD],
            [0xDEAD, 0xBEEF, 0xCAFE, 1, 0, 2, 0xBEEF, 0xDEAD, 0xCAFE],
            [0xDEAD, 0xBEEF, 0xCAFE, 2, 1, 0, 0xCAFE, 0xBEEF, 0xDEAD],
            [0xDEAD, 0xBEEF, 0xCAFE, 2, 0, 1, 0xCAFE, 0xDEAD, 0xBEEF],
        ],
    )
