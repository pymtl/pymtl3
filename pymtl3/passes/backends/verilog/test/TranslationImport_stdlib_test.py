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

from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.stdlib.basic_rtl.test.arbiters_test import test_rr_arb_4 as _rr_arb_4
from pymtl3.stdlib.basic_rtl.test.arbiters_test import test_rr_arb_en_4 as _rr_arb_en_4
from pymtl3.stdlib.basic_rtl.test.crossbars_test import test_crossbar3 as _crossbar3
from pymtl3.stdlib.basic_rtl.test.encoders_test import (
    test_encoder_5_directed as _encoder5,
)
from pymtl3.stdlib.queues.test.valrdy_queues_test import test_2entry_normal_Bits as _n2
from pymtl3.stdlib.queues.test.valrdy_queues_test import test_3entry_normal_Bits as _n3
from pymtl3.stdlib.queues.test.valrdy_queues_test import (
    test_bypass_Bits as _bypass_Bits,
)
from pymtl3.stdlib.queues.test.valrdy_queues_test import (
    test_normal_Bits as _normal_Bits,
)
from pymtl3.stdlib.queues.test.valrdy_queues_test import test_pipe_Bits as _pipe_Bits
from pymtl3.stdlib.test_utils import TestVectorSimulator

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

# Swap run_test_queue with modified version that calls the local do_test
def _run_queue_test( do_test, test_func ):

  def _run_test( m, tvs ):
    def tv_in( model, tv ):
      model.enq.val @= tv[0]
      model.enq.msg @= tv[2]
      model.deq.rdy @= tv[4]
    def tv_out( model, tv ):
      if tv[1] != '?': assert model.enq.rdy == tv[1]
      if tv[3] != '?': assert model.deq.val == tv[3]
      if tv[5] != '?': assert model.deq.msg == tv[5]
    m._tvs = tvs
    m._tv_in, m._tv_out = tv_in, tv_out
    do_test( m )

  original_run_test = test_func.__globals__['run_test_queue']
  test_func.__globals__['run_test_queue'] = _run_test
  try:
    test_func()
  finally:
    test_func.__globals__['run_test_queue'] = original_run_test

def test_bypass_Bits( do_test ):
  _run_queue_test( do_test, _bypass_Bits )

def test_pipe_Bits( do_test ):
  _run_queue_test( do_test, _pipe_Bits )

def test_normal_Bits( do_test ):
  _run_queue_test( do_test, _normal_Bits )

def test_2entry_normal_Bits( do_test ):
  _run_queue_test( do_test, _n2 )

def test_3entry_normal_Bits( do_test ):
  _run_queue_test( do_test, _n3 )
