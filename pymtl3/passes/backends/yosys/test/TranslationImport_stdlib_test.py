#=========================================================================
# TranslationImport_stdlib_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 15, 2019
"""Test stdlib RTL components with SystemVerilog translation and import.

We reuse all the test cases from stdlib test files. To achieve this I
overwrite the original reference to the test function used in stdlib test
files and add my own test function (the `run_test`s). However we need
to make sure the orignal reference is not lost and is restored after
finishing each test (no matter it fails or passes).
"""

from pymtl3.passes.PassGroups import DefaultPassGroup

from pymtl3.passes.backends.verilog.test.TranslationImport_stdlib_test import (
    test_arbiter_rr_arb_4,
    test_arbiter_rr_arb_en_4,
    test_crossbar3,
    test_encoder_5_directed,
)
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.stdlib.test_utils import TestVectorSimulator

from pymtl3.stdlib.stream.test.queues_test import test_normal1_simple as _n1
from pymtl3.stdlib.stream.test.queues_test import test_normal2_simple as _n2
from pymtl3.stdlib.stream.test.queues_test import test_bypass1_simple as _b1
from pymtl3.stdlib.stream.test.queues_test import test_pipe1_simple as _p1

from ..YosysTranslationImportPass import YosysTranslationImportPass


def local_do_test( _m ):
  _m.elaborate()
  # Mark component `_m` as to be translated and imported
  _m.set_metadata( YosysTranslationImportPass.enable, True )
  m = YosysTranslationImportPass()( _m )
  sim = TestVectorSimulator( m, _m._tvs, _m._tv_in, _m._tv_out )
  sim.run_test()

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
      obj.set_metadata( YosysTranslationImportPass.enable, True )

    th = YosysTranslationImportPass()( th )

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
