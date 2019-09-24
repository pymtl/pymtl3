#=========================================================================
# ImportedObject_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 2, 2019
"""Test if the imported object works correctly."""


from pymtl3.datatypes import Bits1, Bits32, Bits64, clog2, mk_bits
from pymtl3.dsl import Component, InPort, Interface, OutPort, Placeholder, connect
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog import ImportConfigs, ImportPass
from pymtl3.passes.sverilog.util.utility import get_dir
from pymtl3.stdlib.test import TestVectorSimulator


def local_do_test( _m ):
  _m.elaborate()
  ipass = ImportPass()
  _m.sverilog_import.fill_missing( _m )
  m = ipass.get_imported_object( _m )
  sim = TestVectorSimulator( m, _m._test_vectors, _m._tv_in, _m._tv_out )
  sim.run_test()

def test_reg( do_test ):
  def tv_in( m, test_vector ):
    m.in_ = Bits32( test_vector[0] )
  def tv_out( m, test_vector ):
    if test_vector[1] != '*':
      assert m.out == Bits32( test_vector[1] )
  class VReg( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.sverilog_import = ImportConfigs(
          vl_src = get_dir(__file__)+'VReg.sv',
          port_map = {
            "clk" : "clk",
            "reset" : "reset",
            "in_" : "d",
            "out" : "q",
          }
      )
  a = VReg()
  a._test_vectors = [
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
  def tv_in( m, test_vector ):
    m.in0 = Bits32( test_vector[0] )
    m.in1 = Bits32( test_vector[1] )
    m.cin = Bits1( test_vector[2] )
  def tv_out( m, test_vector ):
    if test_vector[3] != '*':
      assert m.out == Bits32( test_vector[3] )
    if test_vector[4] != '*':
      assert m.cout == Bits32( test_vector[4] )
  class VAdder( Component ):
    def construct( s ):
      s.in0 = InPort( Bits32 )
      s.in1 = InPort( Bits32 )
      s.cin = InPort( Bits1 )
      s.out = OutPort( Bits32 )
      s.cout = OutPort( Bits1 )
      s.sverilog_import = ImportConfigs(vl_src = get_dir(__file__)+'VAdder.sv')
  a = VAdder()
  a._test_vectors = [
    [    1,      1,     1,     3, 0 ],
    [    1,     -1,     0,     0, 1 ],
    [   42,     42,     1,    85, 0 ],
    [   42,    -43,     1,     0, 1 ],
  ]
  a._tv_in = tv_in
  a._tv_out = tv_out
  do_test( a )

def test_normal_queue( do_test ):
  def tv_in( m, tv ):
    m.enq_en = Bits1( tv[0] )
    m.enq_msg = Bits32( tv[1] )
    m.deq_en = Bits1( tv[3] )
  def tv_out( m, tv ):
    if tv[2] != '*':
      assert m.enq_rdy == Bits1( tv[2] )
    if tv[4] != '*':
      assert m.deq_rdy == Bits1( tv[5] )
    if tv[5] != '*':
      assert m.deq_msg == Bits32( tv[4] )
  class VQueue( Placeholder, Component ):
    def construct( s, data_width, num_entries, count_width ):
      s.count   =  OutPort( mk_bits( count_width )  )
      s.deq_en  =  InPort( Bits1  )
      s.deq_rdy = OutPort( Bits1  )
      s.deq_msg = OutPort( mk_bits( data_width ) )
      s.enq_en  =  InPort( Bits1  )
      s.enq_rdy = OutPort( Bits1  )
      s.enq_msg =  InPort( mk_bits( data_width ) )
      s.sverilog_import = ImportConfigs(vl_src = get_dir(__file__)+'VQueue.sv')
  num_entries = 1
  q = VQueue(
      data_width = 32,
      num_entries = num_entries,
      count_width = clog2(num_entries+1))
  # q.dump_vcd = True
  test_vector = [
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
  q._test_vectors = test_vector
  q._tv_in = tv_in
  q._tv_out = tv_out
  do_test( q )
