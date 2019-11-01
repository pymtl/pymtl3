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

from pymtl3.datatypes import Bits1, clog2, mk_bits
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog import TranslationImportPass
from pymtl3.stdlib.rtl.arbiters_test import test_rr_arb_4 as _rr_arb_4
from pymtl3.stdlib.rtl.arbiters_test import test_rr_arb_en_4 as _rr_arb_en_4
from pymtl3.stdlib.rtl.Crossbar_test import test_crossbar3 as _crossbar3
from pymtl3.stdlib.rtl.Encoder_test import test_encoder_5_directed as _encoder5
from pymtl3.stdlib.rtl.valrdy_queues_test import test_2entry_normal_Bits as _n2
from pymtl3.stdlib.rtl.valrdy_queues_test import test_3entry_normal_Bits as _n3
from pymtl3.stdlib.rtl.valrdy_queues_test import test_bypass_Bits as _bypass_Bits
from pymtl3.stdlib.rtl.valrdy_queues_test import test_normal_Bits as _normal_Bits
from pymtl3.stdlib.rtl.valrdy_queues_test import test_pipe_Bits as _pipe_Bits
from pymtl3.stdlib.test import TestVectorSimulator


def local_do_test( _m ):
  try:
    _m.elaborate()
    # Mark component `_m` as to be translated and imported
    _m.sverilog_translate_import = True
    m = TranslationImportPass()( _m )
    sim = TestVectorSimulator( m, _m._test_vectors, _m._tv_in, _m._tv_out )
    sim.run_test()
  finally:
    try:
      # Explicitly finalize imported component to avoid shared lib name aliasing
      m.finalize()
    except UnboundLocalError:
      # This test fails due to translation errors
      pass

def test_arbiter_rr_arb_4( do_test ):
  # Customized test function
  def run_test( cls, args, test_vectors ):
    m = cls( *args )
    BitsN = mk_bits( args[0] )
    def tv_in( model, test_vector ):
      model.reqs = BitsN(test_vector[0])
    def tv_out( model, test_vector ):
      assert model.grants == BitsN(test_vector[1])
    m._test_vectors = test_vectors
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
  def run_test( cls, args, test_vectors ):
    m = cls( *args )
    BitsN = mk_bits( args[0] )
    def tv_in( model, test_vector ):
      model.en   = Bits1( test_vector[0] )
      model.reqs = BitsN( test_vector[1] )
    def tv_out( model, test_vector ):
      assert model.grants == BitsN(test_vector[2])
    m._test_vectors = test_vectors
    m._tv_in, m._tv_out = tv_in, tv_out
    do_test( m )

  test_func = _rr_arb_en_4
  _run_test = test_func.__globals__['run_en_test']
  test_func.__globals__['run_en_test'] = run_test
  try:
    test_func( None, None )
  finally:
    test_func.__globals__['run_en_test'] = _run_test

def test_crossbar3( do_test ):
  def run_test( cls, args, test_vectors ):
    m = cls( *args )
    T = args[1]
    Tsel = mk_bits( clog2( args[0] ) )

    def tv_in( model, test_vector ):
      n = len( model.in_ )
      for i in range(n):
        model.in_[i] = T(test_vector[i])
        model.sel[i] = Tsel(test_vector[n+i])
    def tv_out( model, test_vector ):
      n = len( model.in_ )
      for i in range(n):
        assert model.out[i] == T(test_vector[n*2+i])
    m._test_vectors = test_vectors
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
  def run_test( m, test_vectors ):
    def tv_in( model, test_vector ):
      model.in_ = test_vector[0]
    def tv_out( model, test_vector ):
      assert model.out == test_vector[1]
    m._test_vectors = test_vectors
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

def _queue_test_tv_in( model, tv ):
  model.enq.val = tv[0]
  model.enq.msg = tv[2]
  model.deq.rdy = tv[4]

def _queue_test_tv_out( model, tv ):
  if tv[1] != '?': assert model.enq.rdy == tv[1]
  if tv[3] != '?': assert model.deq.val == tv[3]
  if tv[5] != '?': assert model.deq.msg == tv[5]

def test_bypass_Bits( do_test ):
  def _run_queue_test( m, test_vectors ):
    m._test_vectors = test_vectors
    m._tv_in, m._tv_out = _queue_test_tv_in, _queue_test_tv_out
    do_test( m )
  test_func = _bypass_Bits
  _run_test = test_func.__globals__['run_test_queue']
  test_func.__globals__['run_test_queue'] = _run_queue_test
  try:
    test_func()
  finally:
    test_func.__globals__['run_test_queue'] = _run_test

def test_pipe_Bits( do_test ):
  def _run_queue_test( m, test_vectors ):
    m._test_vectors = test_vectors
    m._tv_in, m._tv_out = _queue_test_tv_in, _queue_test_tv_out
    do_test( m )
  test_func = _pipe_Bits
  _run_test = test_func.__globals__['run_test_queue']
  test_func.__globals__['run_test_queue'] = _run_queue_test
  try:
    test_func()
  finally:
    test_func.__globals__['run_test_queue'] = _run_test

def test_normal_Bits( do_test ):
  def _run_queue_test( m, test_vectors ):
    m._test_vectors = test_vectors
    m._tv_in, m._tv_out = _queue_test_tv_in, _queue_test_tv_out
    do_test( m )
  test_func = _normal_Bits
  _run_test = test_func.__globals__['run_test_queue']
  test_func.__globals__['run_test_queue'] = _run_queue_test
  try:
    test_func()
  finally:
    test_func.__globals__['run_test_queue'] = _run_test

def test_2entry_normal_Bits( do_test ):
  def _run_queue_test( m, test_vectors ):
    m._test_vectors = test_vectors
    m._tv_in, m._tv_out = _queue_test_tv_in, _queue_test_tv_out
    do_test( m )
  test_func = _n2
  _run_test = test_func.__globals__['run_test_queue']
  test_func.__globals__['run_test_queue'] = _run_queue_test
  try:
    test_func()
  finally:
    test_func.__globals__['run_test_queue'] = _run_test

def test_3entry_normal_Bits( do_test ):
  def _run_queue_test( m, test_vectors ):
    m._test_vectors = test_vectors
    m._tv_in, m._tv_out = _queue_test_tv_in, _queue_test_tv_out
    do_test( m )
  test_func = _n3
  _run_test = test_func.__globals__['run_test_queue']
  test_func.__globals__['run_test_queue'] = _run_queue_test
  try:
    test_func()
  finally:
    test_func.__globals__['run_test_queue'] = _run_test
