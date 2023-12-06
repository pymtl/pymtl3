import pytest
from hypothesis import given, settings
from hypothesis.strategies import lists, tuples, composite, sampled_from

from pymtl3 import *
from pymtl3.datatypes import strategies as pst
from pymtl3.stdlib.test_utils import run_spec_sim

from .Adder import Adder
from .RegIncr import RegIncr

#-----------------------------------------------------------------------
# Directed parameters, directed values
#-----------------------------------------------------------------------

@pytest.mark.parametrize(
  "alist, blist", [
    # Parametrized test case #1
    ([12, 41, 19], [13, 12, 15]),
    # Parametrized test case #2
    ([41, 88, 16], [12, 32, 12]),
    # Parametrized test case #3
    ([19, 91], [15, 88]),
  ]
)
def test_adder_dp_dv( alist, blist ):
  run_spec_sim( (Adder, 16), a=alist, b=blist )

@pytest.mark.parametrize(
  "inlist", [
    # Parametrized test case #1
    ([12, 41, 19]),
    # Parametrized test case #2
    ([41, 88, 16]),
    # Parametrized test case #3
    ([19, 91]),
  ]
)
def test_regincr_dp_dv( inlist ):
  run_spec_sim( (RegIncr, 16), in_=inlist )

#-----------------------------------------------------------------------
# Directed parameters, random values
#-----------------------------------------------------------------------

@given(
  ablist = lists( tuples( pst.bits(16), pst.bits(16) ), min_size=10 )
)
@settings(deadline=None)
def test_adder_dp_rv( ablist ):
  a, b = zip(*ablist)
  run_spec_sim( (Adder, 16), a=a, b=b )

@given(
  inlist = lists( pst.bits(16), min_size=5 )
)
@settings(deadline=None)
def test_regincr_dp_rv( inlist ):
  run_spec_sim( (RegIncr, 16), in_=inlist )

#-----------------------------------------------------------------------
# Random parameters, random values
#-----------------------------------------------------------------------

@composite
def nbits_and_ablist( draw ):
  nbits = draw(sampled_from([1, 2, 8, 15, 32]))
  ablist = draw(lists(tuples(pst.bits(nbits), pst.bits(nbits)), min_size=1))
  return (nbits, ablist)

@given(
  nbits_and_ablist = nbits_and_ablist()
)
@settings(deadline=None)
def test_adder_rp_rv( nbits_and_ablist ):
  nbits, ablist = nbits_and_ablist
  a, b = zip(*ablist)
  run_spec_sim( (Adder, nbits), a=a, b=b )

@composite
def nbits_and_inlist( draw ):
  nbits = draw(sampled_from([1, 2, 8, 15, 32]))
  inlist = draw(lists(pst.bits(nbits), min_size=1))
  return (nbits, inlist)

@given(
  nbits_and_inlist = nbits_and_inlist()
)
@settings(deadline=None)
def test_regincr_rp_rv( nbits_and_inlist ):
  nbits, inlist = nbits_and_inlist
  run_spec_sim( (RegIncr, nbits), in_=inlist )
