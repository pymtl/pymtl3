#=========================================================================
# TranslationImport_stdlib_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 3, 2019
"""Test stdlib RTL components with SystemVerilog translation and import.

We reuse all the test cases from stdlib test files. To achieve this I
overwrite the original reference to the test function used in stdlib test
files and add my own test function (the `run_test`s). However we need
to make sure the orignal reference is not lost and is restored after
finishing each test (no matter it fails or passes).
"""

from pymtl3.passes.PassGroups import DefaultPassGroup

from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.stdlib.primitive.test.arbiters_test import test_rr_arb_4 as _rr_arb_4
from pymtl3.stdlib.primitive.test.arbiters_test import test_rr_arb_en_4 as _rr_arb_en_4
from pymtl3.stdlib.primitive.test.crossbars_test import test_crossbar3 as _crossbar3
from pymtl3.stdlib.primitive.test.encoders_test import (
    test_encoder_5_directed as _encoder5,
)
from pymtl3.stdlib.stream.test.queues_test import test_normal1_simple as _n1
from pymtl3.stdlib.stream.test.queues_test import test_normal2_simple as _n2
from pymtl3.stdlib.stream.test.queues_test import test_bypass1_simple as _b1
from pymtl3.stdlib.stream.test.queues_test import test_pipe1_simple as _p1
from pymtl3.stdlib.test_utils import TestVectorSimulator
from pymtl3.stdlib.test_utils import run_sim as stdlib_run_sim

from ..VerilogTranslationImportPass import VerilogTranslationImportPass


def local_do_test( _m ):
  _m.elaborate()
  # Mark component `_m` as to be translated and imported
  _m.set_metadata( VerilogTranslationImportPass.enable, True )
  m = VerilogTranslationImportPass()( _m )
  sim = TestVectorSimulator( m, _m._tvs, _m._tv_in, _m._tv_out )
  sim.run_test()

def test_arbiter_rr_arb_4( do_test ):
  # Customized test function
  def run_test( m, tvs ):
    def tv_in( model, tv ):
      model.reqs @= tv[0]
    def tv_out( model, tv ):
      assert model.grants == tv[1]
    m._tvs = tvs
    m._tv_in, m._tv_out = tv_in, tv_out
    do_test( m )

  # Swap in the customized test method
  test_func = _rr_arb_4
  _run_test = test_func.__globals__['run_test']
  test_func.__globals__['run_test'] = run_test
  try:
    test_func()
  finally:
    # Restore the original method regardless of the test result
    test_func.__globals__['run_test'] = _run_test

def test_arbiter_rr_arb_en_4( do_test ):
  def run_test( m, tvs ):
    def tv_in( model, tv ):
      model.en   @= tv[0]
      model.reqs @= tv[1]
    def tv_out( model, tv ):
      assert model.grants == tv[2]
    m._tvs = tvs
    m._tv_in, m._tv_out = tv_in, tv_out
    do_test( m )

  test_func = _rr_arb_en_4
  _run_test = test_func.__globals__['run_en_test']
  test_func.__globals__['run_en_test'] = run_test
  try:
    test_func( None )
  finally:
    test_func.__globals__['run_en_test'] = _run_test

def test_crossbar3( do_test ):
  def run_test( m, tvs ):
    def tv_in( model, tv ):
      n = len( model.in_ )
      for i in range(n):
        model.in_[i] @= tv[i]
        model.sel[i] @= tv[n+i]
    def tv_out( model, tv ):
      n = len( model.in_ )
      for i in range(n):
        assert model.out[i] == tv[n*2+i]
    m._tvs = tvs
    m._tv_in, m._tv_out = tv_in, tv_out
    do_test( m )

  test_func = _crossbar3
  _run_test = test_func.__globals__['run_test_crossbar']
  test_func.__globals__['run_test_crossbar'] = run_test
  try:
    test_func()
  finally:
    test_func.__globals__['run_test_crossbar'] = _run_test

def test_encoder_5_directed( do_test ):
  def run_test( m, tvs ):
    def tv_in( model, tv ):
      model.in_ @= tv[0]
    def tv_out( model, tv ):
      assert model.out == tv[1]
    m._tvs = tvs
    m._tv_in, m._tv_out = tv_in, tv_out
    do_test( m )

  test_func = _encoder5
  _run_test = test_func.__globals__['run_test']
  test_func.__globals__['run_test'] = run_test
  try:
    test_func()
  finally:
    test_func.__globals__['run_test'] = _run_test

#-------------------------------------------------------------------------
# Queue tests
#-------------------------------------------------------------------------

# Swap run_test_queue with modified version that calls the local run_sim
def _run_queue_test( test_func ):

  def _run_sim( th, cmdline_opts, duts ):
    th.elaborate()
    dut_objs = []

    for dut in duts:
      dut_objs.append( eval(f'th.{dut}') )

    for obj in dut_objs:
      obj.set_metadata( VerilogTranslationImportPass.enable, True )

    th = VerilogTranslationImportPass()( th )

    th.apply( DefaultPassGroup() )
    th.sim_reset()

    while not th.done() and th.sim_cycle_count() < 100:
      th.sim_tick()

    assert th.sim_cycle_count() < 100

  original_run_sim = test_func.__globals__['run_sim']
  test_func.__globals__['run_sim'] = _run_sim
  try:
    test_func( None )
  finally:
    test_func.__globals__['run_sim'] = original_run_sim

def test_normal1_simple():
  _run_queue_test( _n1 )

def test_normal2_simple():
  _run_queue_test( _n2 )

def test_bypass1_simple():
  _run_queue_test( _b1 )

def test_pipe1_simple():
  _run_queue_test( _p1 )
