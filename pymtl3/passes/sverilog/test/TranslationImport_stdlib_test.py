#=========================================================================
# TranslationImport_stdlib_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 3, 2019
"""Test stdlib RTL components with SystemVerilog translation and import."""

from pymtl3.datatypes import mk_bits, Bits1

from pymtl3.passes.sverilog import TranslationPass
from pymtl3.passes.sverilog.import_.ImportPass import get_imported_object
from pymtl3.stdlib.test import TestVectorSimulator
from pymtl3.passes.rtlir.util.test_utility import do_test

from pymtl3.stdlib.rtl.arbiters_test import test_rr_arb_4 as _rr_arb_4
from pymtl3.stdlib.rtl.arbiters_test import test_rr_arb_en_4 as _rr_arb_en_4
from pymtl3.stdlib.rtl.Crossbar_test import test_crossbar3 as _crossbar3
from pymtl3.stdlib.rtl.Encoder_test import test_encoder_5_directed as _encoder5
from pymtl3.stdlib.rtl.valrdy_queues_test import test_bypass_int as _bypass_int
from pymtl3.stdlib.rtl.valrdy_queues_test import test_bypass_Bits as _bypass_Bits
from pymtl3.stdlib.rtl.valrdy_queues_test import test_pipe_int as _pipe_int
from pymtl3.stdlib.rtl.valrdy_queues_test import test_pipe_Bits as _pipe_Bits
from pymtl3.stdlib.rtl.valrdy_queues_test import test_normal_int as _normal_int
from pymtl3.stdlib.rtl.valrdy_queues_test import test_normal_Bits as _normal_Bits
from pymtl3.stdlib.rtl.valrdy_queues_test import test_2entry_normal_Bits as _normal_Bits_2
from pymtl3.stdlib.rtl.valrdy_queues_test import test_3entry_normal_Bits as _normal_Bits_3

def local_do_test( _m ):
  _m.elaborate()
  _m.apply( TranslationPass() )
  m = get_imported_object( _m )
  sim = TestVectorSimulator( m, _m._test_vectors, _m._tv_in, _m._tv_out )
  sim.run_test()

def test_arbiter_rr_arb_4( do_test ):
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

  test_func = _rr_arb_4
  test_func.__globals__['run_test'] = run_test
  test_func()

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
  test_func.__globals__['run_en_test'] = run_test
  test_func( None, None )

def test_crossbar3( do_test ):
  def run_test( cls, args, test_vectors ):
    m = cls( *args )
    T = args[1]
    def tv_in( model, test_vector ):
      n = len( model.in_ )
      for i in range(n):
        model.in_[i] = T(test_vector[i])
        model.sel[i] = T(test_vector[n+i])
    def tv_out( model, test_vector ):
      n = len( model.in_ )
      for i in range(n):
        assert model.out[i] == T(test_vector[n*2+i])
    m._test_vectors = test_vectors
    m._tv_in, m._tv_out = tv_in, tv_out
    do_test( m )

  test_func = _crossbar3
  test_func.__globals__['run_test_crossbar'] = run_test
  test_func()

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
  test_func.__globals__['run_test'] = run_test
  test_func()

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
  test_func.__globals__['run_test_queue'] = _run_queue_test
  test_func()

def test_pipe_Bits( do_test ):
  def _run_queue_test( m, test_vectors ):
    m._test_vectors = test_vectors
    m._tv_in, m._tv_out = _queue_test_tv_in, _queue_test_tv_out
    do_test( m )
  test_func = _pipe_Bits
  test_func.__globals__['run_test_queue'] = _run_queue_test
  test_func()

def test_normal_Bits( do_test ):
  def _run_queue_test( m, test_vectors ):
    m._test_vectors = test_vectors
    m._tv_in, m._tv_out = _queue_test_tv_in, _queue_test_tv_out
    do_test( m )
  test_func = _normal_Bits
  test_func.__globals__['run_test_queue'] = _run_queue_test
  test_func()

def test_2entry_normal_Bits( do_test ):
  def _run_queue_test( m, test_vectors ):
    m._test_vectors = test_vectors
    m._tv_in, m._tv_out = _queue_test_tv_in, _queue_test_tv_out
    do_test( m )
  test_func = _normal_Bits_2
  test_func.__globals__['run_test_queue'] = _run_queue_test
  test_func()

def test_3entry_normal_Bits( do_test ):
  def _run_queue_test( m, test_vectors ):
    m._test_vectors = test_vectors
    m._tv_in, m._tv_out = _queue_test_tv_in, _queue_test_tv_out
    do_test( m )
  test_func = _normal_Bits_3
  test_func.__globals__['run_test_queue'] = _run_queue_test
  test_func()