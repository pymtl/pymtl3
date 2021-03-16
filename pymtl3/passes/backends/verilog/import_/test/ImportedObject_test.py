#=========================================================================
# ImportedObject_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 2, 2019
"""Test if the imported object works correctly."""

import gc
from os.path import dirname

import pytest

from pymtl3 import DefaultPassGroup, Interface
from pymtl3.datatypes import Bits1, Bits10, Bits32, Bits48, Bits64, clog2, mk_bits
from pymtl3.dsl import Component, InPort, Interface, OutPort, connect
from pymtl3.passes.backends.verilog import (
    VerilogPlaceholder,
    VerilogPlaceholderPass,
    VerilogTranslationImportPass,
    VerilogVerilatorImportPass,
)
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.stdlib.test_utils import TestVectorSimulator


def local_do_test( _m ):
  _m.elaborate()
  if not hasattr( _m, "_no_trans_import" ):
    _m.set_metadata( VerilogTranslationImportPass.enable, True )
  _m.apply( VerilogPlaceholderPass() )
  m = VerilogTranslationImportPass()( _m )
  sim = TestVectorSimulator( m, _m._tvs, _m._tv_in, _m._tv_out )
  sim.run_test()

def test_reg( do_test ):
  # General trans-import test
  def tv_in( m, tv ):
    m.in_ @= Bits32( tv[0] )
  def tv_out( m, tv ):
    if tv[1] != '*':
      assert m.out == Bits32( tv[1] )
  class VReg( Component, VerilogPlaceholder ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.set_metadata( VerilogPlaceholderPass.port_map, {
          s.clk : "clk", s.reset : "reset",
          s.in_ : "d",   s.out : "q",
      } )
  a = VReg()
  a._tvs = [
    [    1,    '*' ],
    [    2,      1 ],
    [   -1,      2 ],
    [   -2,     -1 ],
    [   42,     -2 ],
    [  -42,     42 ],
  ]
  a._tv_in = tv_in
  a._tv_out = tv_out
  do_test( a )

def test_vl_uninit( do_test ):
  # Use a latch to test if verilator has correctly set up
  # the inital signal values
  def tv_in( m, tv ):
    m.in_ @= Bits32( tv[0] )
  def tv_out( m, tv ):
    assert m.out == Bits32( tv[1] )
  class VUninit( Component, VerilogPlaceholder ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.set_metadata( VerilogPlaceholderPass.port_map, {
          s.in_ : "d", s.out : "q",
      } )
      s.set_metadata( VerilogVerilatorImportPass.vl_xinit, 'ones' )
  a = VUninit()
  a._tvs = [
    [    0, 4294967295 ],
    [    2, 4294967295 ],
    [   42,         42 ],
  ]
  a._tv_in = tv_in
  a._tv_out = tv_out
  do_test( a )

def test_reg_incomplete_portmap( do_test ):
  # Test support for incomplete port map
  def tv_in( m, tv ):
    m.in_ @= Bits32( tv[0] )
  def tv_out( m, tv ):
    if tv[1] != '*':
      assert m.out == Bits32( tv[1] )
  class VReg( Component, VerilogPlaceholder ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )

      s.set_metadata( VerilogPlaceholderPass.port_map, {
          s.in_ : "d",   s.out : "q",
      } )
  a = VReg()
  a._tvs = [
    [    1,    '*' ],
    [    2,      1 ],
    [   -1,      2 ],
    [   -2,     -1 ],
    [   42,     -2 ],
    [  -42,     42 ],
  ]
  a._tv_in = tv_in
  a._tv_out = tv_out
  do_test( a )

def test_adder( do_test ):
  # Test an adder
  def tv_in( m, tv ):
    m.in0 @= Bits32( tv[0] )
    m.in1 @= Bits32( tv[1] )
    m.cin @= Bits1(  tv[2] )
  def tv_out( m, tv ):
    if tv[3] != '*':
      assert m.out == Bits32( tv[3] )
    if tv[4] != '*':
      assert m.cout == Bits1( tv[4] )
  class VAdder( Component, VerilogPlaceholder ):
    def construct( s ):
      s.in0 = InPort( Bits32 )
      s.in1 = InPort( Bits32 )
      s.cin = InPort( Bits1 )
      s.out = OutPort( Bits32 )
      s.cout = OutPort( Bits1 )
  a = VAdder()
  a._tvs = [
    [    1,      1,     1,     3, 0 ],
    [    1,     -1,     0,     0, 1 ],
    [   42,     42,     1,    85, 0 ],
    [   42,    -43,     1,     0, 1 ],
  ]
  a._tv_in = tv_in
  a._tv_out = tv_out
  do_test( a )

def test_normal_queue_implicit_top_module( do_test ):
  # Test a Placeholder with params in `construct`
  def tv_in( m, tv ):
    m.enq_en @= Bits1( tv[0] )
    m.enq_msg @= Bits32( tv[1] )
    m.deq_en @= Bits1( tv[3] )
  def tv_out( m, tv ):
    if tv[2] != '*':
      assert m.enq_rdy == Bits1( tv[2] )
    if tv[4] != '*':
      assert m.deq_rdy == Bits1( tv[5] )
    if tv[5] != '*':
      assert m.deq_msg == Bits32( tv[4] )
  class VQueue( Component, VerilogPlaceholder ):
    def construct( s, data_width, num_entries, count_width ):
      s.count   =  OutPort( mk_bits( count_width )  )
      s.deq_en  =  InPort( Bits1  )
      s.deq_rdy = OutPort( Bits1  )
      s.deq_msg = OutPort( mk_bits( data_width ) )
      s.enq_en  =  InPort( Bits1  )
      s.enq_rdy = OutPort( Bits1  )
      s.enq_msg =  InPort( mk_bits( data_width ) )
  num_entries = 1
  q = VQueue(
      data_width = 32,
      num_entries = num_entries,
      count_width = clog2(num_entries+1))
  tv = [
    #   enq                deq
    #   en    msg   rdy    en    msg   rdy
    [    1,    42,    1,    0,     0,    0  ],
    [    0,    43,    0,    1,    42,    1  ],
    [    1,    43,    1,    0,    42,    0  ],
    [    0,    44,    0,    1,    43,    1  ],
    [    1,    44,    1,    0,    43,    0  ],
    [    0,    45,    0,    1,    44,    1  ],
    [    1,    45,    1,    0,    44,    0  ],
  ]
  q._tvs = tv
  q._tv_in = tv_in
  q._tv_out = tv_out
  do_test( q )

def test_normal_queue_params( do_test ):
  # Test the `params` option of placeholder configs
  def tv_in( m, tv ):
    m.enq_en @= Bits1( tv[0] )
    m.enq_msg @= Bits32( tv[1] )
    m.deq_en @= Bits1( tv[3] )
  def tv_out( m, tv ):
    if tv[2] != '*':
      assert m.enq_rdy == Bits1( tv[2] )
    if tv[4] != '*':
      assert m.deq_rdy == Bits1( tv[5] )
    if tv[5] != '*':
      assert m.deq_msg == Bits32( tv[4] )
  class Queue( Component, VerilogPlaceholder ):
    def construct( s, nbits, nelems, nbits_cnt ):
      s.count   =  OutPort( mk_bits( nbits_cnt )  )
      s.deq_en  =  InPort( Bits1  )
      s.deq_rdy = OutPort( Bits1  )
      s.deq_msg = OutPort( mk_bits( nbits ) )
      s.enq_en  =  InPort( Bits1  )
      s.enq_rdy = OutPort( Bits1  )
      s.enq_msg =  InPort( mk_bits( nbits ) )
      s.set_metadata( VerilogPlaceholderPass.src_file, dirname(__file__)+'/VQueue.v' )
      s.set_metadata( VerilogPlaceholderPass.top_module, 'VQueue' )
      s.set_metadata( VerilogPlaceholderPass.params, {
          'data_width'  : nbits,
          'num_entries' : nelems,
          'count_width' : nbits_cnt,
      } )
  num_entries = 1
  q = Queue(
      nbits = 32,
      nelems = num_entries,
      nbits_cnt = clog2(num_entries+1))
  tv = [
    #   enq                deq
    #   en    msg   rdy    en    msg   rdy
    [    1,    42,    1,    0,     0,    0  ],
    [    0,    43,    0,    1,    42,    1  ],
    [    1,    43,    1,    0,    42,    0  ],
    [    0,    44,    0,    1,    43,    1  ],
    [    1,    44,    1,    0,    43,    0  ],
    [    0,    45,    0,    1,    44,    1  ],
    [    1,    45,    1,    0,    44,    0  ],
  ]
  q._tvs = tv
  q._tv_in = tv_in
  q._tv_out = tv_out
  do_test( q )

def test_normal_queue_interface( do_test ):
  # Test a Placeholder with params in `construct`
  def tv_in( m, tv ):
    m.enq.en @= Bits1( tv[0] )
    m.enq.msg @= Bits32( tv[1] )
    m.deq.en @= Bits1( tv[3] )
  def tv_out( m, tv ):
    if tv[2] != '*':
      assert m.enq.rdy == Bits1( tv[2] )
    if tv[4] != '*':
      assert m.deq.rdy == Bits1( tv[5] )
    if tv[5] != '*':
      assert m.deq.msg == Bits32( tv[4] )
  class DequeueIfc( Interface ):
    def construct( s, Type ):
      s.en  = InPort( Bits1 )
      s.rdy = OutPort( Bits1 )
      s.msg = OutPort( Type )
  class EnqueueIfc( Interface ):
    def construct( s, Type ):
      s.en  = InPort( Bits1 )
      s.rdy = OutPort( Bits1 )
      s.msg = InPort( Type )
  class VQueue( Component, VerilogPlaceholder ):
    def construct( s, data_width, num_entries, count_width ):
      s.count = OutPort( mk_bits( count_width )  )
      s.deq   = DequeueIfc( mk_bits( data_width ) )
      s.enq   = EnqueueIfc( mk_bits( data_width ) )
  num_entries = 1
  q = VQueue(
      data_width = 32,
      num_entries = num_entries,
      count_width = clog2(num_entries+1))
  tv = [
    #   enq                deq
    #   en    msg   rdy    en    msg   rdy
    [    1,    42,    1,    0,     0,    0  ],
    [    0,    43,    0,    1,    42,    1  ],
    [    1,    43,    1,    0,    42,    0  ],
    [    0,    44,    0,    1,    43,    1  ],
    [    1,    44,    1,    0,    43,    0  ],
    [    0,    45,    0,    1,    44,    1  ],
    [    1,    45,    1,    0,    44,    0  ],
  ]
  q._tvs = tv
  q._tv_in = tv_in
  q._tv_out = tv_out
  do_test( q )

def test_unpacked_port_array( do_test ):
  # Test the `params` option of placeholder configs
  def tv_in( m, tv ):
    m.in_[0] @= Bits32(tv[0])
    m.in_[1] @= Bits32(tv[1])
  def tv_out( m, tv ):
    assert m.out[0] == Bits32(tv[2])
    assert m.out[1] == Bits32(tv[3])
  class VPassThrough( Component, VerilogPlaceholder ):
    def construct( s, nports, nbits ):
      s.in_ = [ InPort( mk_bits(nbits) ) for _ in range(nports) ]
      s.out = [ OutPort( mk_bits(nbits) ) for _ in range(nports) ]
      s.set_metadata( VerilogPlaceholderPass.params, {
          'num_ports' : nports,
          'bitwidth'  : nbits,
      } )
      s.set_metadata( VerilogPlaceholderPass.has_clk, False )
      s.set_metadata( VerilogPlaceholderPass.has_reset, False )

  q = VPassThrough( 2, 32 )
  tv = [
    [ 1, 42, 1, 42 ],
    [ 1, -1, 1, -1 ],
    [ 0,  1, 0,  1 ],
    [ -1, 1, -1, 1 ],
  ]
  q._tvs = tv
  q._tv_in = tv_in
  q._tv_out = tv_out
  do_test( q )

def test_unpacked_port_array_infer_clk_reset( do_test ):
  # Test the `params` option of placeholder configs
  def tv_in( m, tv ):
    m.in_[0] @= Bits32(tv[0])
    m.in_[1] @= Bits32(tv[1])
  def tv_out( m, tv ):
    assert m.out[0] == Bits32(tv[2])
    assert m.out[1] == Bits32(tv[3])
  class VPassThrough( Component, VerilogPlaceholder ):
    def construct( s, nports, nbits ):
      s.in_ = [ InPort( mk_bits(nbits) ) for _ in range(nports) ]
      s.out = [ OutPort( mk_bits(nbits) ) for _ in range(nports) ]
      s.set_metadata( VerilogPlaceholderPass.params, {
          'num_ports' : nports,
          'bitwidth'  : nbits,
      } )

  q = VPassThrough( 2, 32 )
  tv = [
    [ 1, 42, 1, 42 ],
    [ 1, -1, 1, -1 ],
    [ 0,  1, 0,  1 ],
    [ -1, 1, -1, 1 ],
  ]
  q._tvs = tv
  q._tv_in = tv_in
  q._tv_out = tv_out
  do_test( q )

@pytest.mark.parametrize(
  "translate", [ True, False ]
)
def test_param_pass_through( do_test, translate ):
  class VPassThrough( Component, VerilogPlaceholder ):
    def construct( s, nports, nbits ):
      s.in_ = [ InPort( mk_bits(nbits) ) for _ in range(nports) ]
      s.out = [ OutPort( mk_bits(nbits) ) for _ in range(nports) ]
      s.set_metadata( VerilogPlaceholderPass.params, {
          'num_ports' : nports,
          'bitwidth'  : nbits,
      } )
      s.set_metadata( VerilogPlaceholderPass.has_clk, False )
      s.set_metadata( VerilogPlaceholderPass.has_reset, False )
  class PassThrough( Component ):
    def construct( s ):
      s.in_ = InPort( Bits48 )
      s.out = OutPort( Bits48 )
      s.pt16 = VPassThrough(1, 16)
      s.pt32 = VPassThrough(1, 32)
      s.pt16.in_[0] //= s.in_[0:16]
      s.pt16.out[0] //= s.out[0:16]
      s.pt32.in_[0] //= s.in_[16:48]
      s.pt32.out[0] //= s.out[16:48]
    def line_trace( s ):
      return f"{s.in_} > {s.out}"
  def tv_in( m, tv ):
    m.in_ @= Bits48( tv[0] )
  def tv_out( m, tv ):
    assert m.out == Bits48( tv[1] )

  p = PassThrough()
  tv = [
    [  1,  1, ],
    [ -1, -1, ],
    [ 42, 42, ],
    [ -2, -2, ],
  ]
  p._tvs = tv
  p._tv_in = tv_in
  p._tv_out = tv_out
  if not translate:
    p._no_trans_import = True
  do_test( p )

def test_non_top_portmap( do_test ):
  def tv_in( m, tv ):
    m.in_ @= Bits32(tv[0])
  def tv_out( m, tv ):
    if tv[1] != '*':
      assert m.out == Bits32(tv[1])
  class VReg( Component, VerilogPlaceholder ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.set_metadata( VerilogPlaceholderPass.port_map, {
          s.in_ : "d", s.out : "q",
      } )
  class Top( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.v = VReg()
      s.v.in_ //= s.in_
      s.v.out //= s.out
  a = Top()
  a._tvs = [
    [    1,    '*' ],
    [    2,      1 ],
    [   -1,      2 ],
    [   -2,     -1 ],
    [   42,     -2 ],
    [  -42,     42 ],
  ]
  a._tv_in = tv_in
  a._tv_out = tv_out
  do_test( a )

#-------------------------------------------------------------------------
# test cases that do not use do_test
#-------------------------------------------------------------------------

def test_reg_external_trace( do_test ):
  # Test Verilog line trace
  class VRegTrace( Component, VerilogPlaceholder ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.set_metadata( VerilogPlaceholderPass.port_map, {
          s.in_ : "d", s.out : "q",
      } )
      s.set_metadata( VerilogVerilatorImportPass.vl_line_trace, True )
      s.set_metadata( VerilogTranslationImportPass.enable, True )
  a = VRegTrace()
  a.elaborate()
  a.apply( VerilogPlaceholderPass() )
  a = VerilogTranslationImportPass()( a )
  a.apply( DefaultPassGroup() )

  assert a.line_trace() == 'q =          0'
  a.in_ @= Bits32(1)
  a.sim_tick()
  assert a.line_trace() == 'q =          1'
  a.in_ @= Bits32(2)
  a.sim_tick()
  assert a.line_trace() == 'q =          2'
  a.in_ @= Bits32(-1)
  a.sim_tick()
  # 0xFFFFFFFF unsigned
  assert a.line_trace() == 'q = 4294967295'
  a.sim_tick()
  a.finalize()

def test_reg_infer_external_trace( do_test ):
  # Test Verilog line trace
  class VRegTrace( Component, VerilogPlaceholder ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.set_metadata( VerilogPlaceholderPass.port_map, {
          s.in_ : "d", s.out : "q",
      } )
      s.set_metadata( VerilogTranslationImportPass.enable, True )
  a = VRegTrace()
  a.elaborate()
  a.apply( VerilogPlaceholderPass() )
  a = VerilogTranslationImportPass()( a )
  a.apply( DefaultPassGroup() )

  assert a.line_trace() == 'q =          0'
  a.in_ @= Bits32(1)
  a.sim_tick()
  assert a.line_trace() == 'q =          1'
  a.in_ @= Bits32(2)
  a.sim_tick()
  assert a.line_trace() == 'q =          2'
  a.in_ @= Bits32(-1)
  a.sim_tick()
  # 0xFFFFFFFF unsigned
  assert a.line_trace() == 'q = 4294967295'
  a.sim_tick()
  a.finalize()

def test_incr_on_demand_vcd( do_test ):
  class VIncr( Component, VerilogPlaceholder ):
    def construct( s ):
      s.in_ = InPort( 10 )
      s.out = OutPort( 10 )
      s.vcd_en = OutPort()
      s.set_metadata( VerilogPlaceholderPass.has_clk, False )
      s.set_metadata( VerilogPlaceholderPass.has_reset, False )
      s.set_metadata( VerilogVerilatorImportPass.vl_trace, True )
      s.set_metadata( VerilogVerilatorImportPass.vl_trace_on_demand, True )
      s.set_metadata( VerilogVerilatorImportPass.vl_trace_on_demand_portname, "vcd_en" )
  a = VIncr()
  a.elaborate()
  a.apply( VerilogPlaceholderPass() )
  a = VerilogTranslationImportPass()( a )
  a.apply( DefaultPassGroup() )

  for i in range(64):
    a.in_ @= Bits10(i)
    a.sim_tick()

  a.finalize()
