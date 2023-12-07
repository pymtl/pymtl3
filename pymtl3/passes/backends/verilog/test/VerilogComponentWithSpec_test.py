import pytest
from hypothesis import given, settings
from hypothesis.strategies import lists, tuples, composite, sampled_from

from pymtl3 import *
from pymtl3.datatypes import strategies as pst
from pymtl3.stdlib.test_utils import gen_vector_spec_test_harness

from .Adder import Adder
from .RegIncr import RegIncr

#-----------------------------------------------------------------------
# Directed parameters, directed values
#-----------------------------------------------------------------------

def adder_apply_input_vector( model, input_vector_map ):
  model.a @= input_vector_map["a"]
  model.b @= input_vector_map["b"]

def adder_check_output_vector( dut, ref ):
  assert dut.sum == ref.sum

def regincr_apply_input_vector( model, input_vector_map ):
  model.in_ @= input_vector_map["in_"]

def regincr_check_output_vector( dut, ref ):
  assert dut.out == ref.out

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
  th = gen_vector_spec_test_harness(
         Adder(16),
         input_vector_list_map = {
           "a" : alist,
           "b" : blist,
         },
         apply_input_func = adder_apply_input_vector,
         check_output_func = adder_check_output_vector,
       )
  th.run_sim()

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
  th = gen_vector_spec_test_harness(
         RegIncr(16),
         input_vector_list_map = {
           "in_" : inlist,
         },
         apply_input_func = regincr_apply_input_vector,
         check_output_func = regincr_check_output_vector,
       )
  th.run_sim()

#-----------------------------------------------------------------------
# Directed parameters, random values
#-----------------------------------------------------------------------

@given(
  ablist = lists( tuples( pst.bits(16), pst.bits(16) ), min_size=10 )
)
@settings(deadline=None)
def test_adder_dp_rv( ablist ):
  alist, blist = zip(*ablist)
  th = gen_vector_spec_test_harness(
         Adder(16),
         input_vector_list_map = {
           "a" : alist,
           "b" : blist,
         },
       )
  th.run_sim()

@given(
  inlist = lists( pst.bits(16), min_size=5 )
)
@settings(deadline=None)
def test_regincr_dp_rv( inlist ):
  th = gen_vector_spec_test_harness(
         RegIncr(16),
         input_vector_list_map = {
           "in_" : inlist,
         },
       )
  th.run_sim()

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
  alist, blist = zip(*ablist)
  th = gen_vector_spec_test_harness(
         Adder(nbits),
         input_vector_list_map = {
           "a" : alist,
           "b" : blist,
         },
       )
  th.run_sim()

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
  th = gen_vector_spec_test_harness(
         RegIncr(nbits),
         input_vector_list_map = {
           "in_" : inlist,
         },
       )
  th.run_sim()
