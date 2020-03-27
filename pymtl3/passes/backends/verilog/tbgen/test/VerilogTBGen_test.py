#=========================================================================
# ImportedObject_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 2, 2019
"""Test if the imported object works correctly."""

from os.path import dirname

import pytest

from pymtl3 import SimulationPass
from pymtl3.datatypes import Bits1, Bits32, Bits48, Bits64, clog2, mk_bits
from pymtl3.dsl import Component, InPort, Interface, OutPort, Placeholder, connect
from pymtl3.passes.backends.verilog import (
    TranslationConfigs,
    TranslationImportPass,
    VerilatorImportConfigs,
    VerilogPlaceholderConfigs,
    VerilogPlaceholderPass,
    VerilogTBGenPass,
)
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.stdlib.test import TestVectorSimulator

from ...testcases import CaseConnectArrayBits32FooIfcComp


def local_do_test( _m ):
  _m.elaborate()
  _m.apply( VerilogPlaceholderPass() )
  m = TranslationImportPass()( _m )
  m.verilog_tbgen = '1234'
  m.apply( VerilogTBGenPass() )
  sim = TestVectorSimulator( m, _m._test_vectors, _m._tv_in, _m._tv_out )
  sim.run_test()

def test_normal_queue( do_test ):
  # Test a Placeholder with params in `construct`
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
  class Queue( Component, Placeholder ):
    def construct( s, data_width, num_entries, count_width ):
      s.count   =  OutPort( mk_bits( count_width )  )
      s.deq_en  =  InPort( Bits1  )
      s.deq_rdy = OutPort( Bits1  )
      s.deq_msg = OutPort( mk_bits( data_width ) )
      s.enq_en  =  InPort( Bits1  )
      s.enq_rdy = OutPort( Bits1  )
      s.enq_msg =  InPort( mk_bits( data_width ) )
      s.config_placeholder = VerilogPlaceholderConfigs(
          src_file = dirname(__file__)+'/VQueue.v',
          top_module = 'VQueue',
      )
      s.verilog_translate_import = True
  num_entries = 1
  q = Queue(
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

def test_CaseConnectArrayBits32FooIfcComp():
  case = CaseConnectArrayBits32FooIfcComp
  try:
    _m = case.DUT()
    _m.elaborate()
    _m.verilog_translate_import = True
    _m.apply( VerilogPlaceholderPass() )
    m = TranslationImportPass()( _m )
    m.verilog_tbgen = True
    m.apply( VerilogTBGenPass() )
    sim = TestVectorSimulator( m, case.TEST_VECTOR, case.TV_IN, case.TV_OUT )
    sim.run_test()
  finally:
    try:
      m.finalize()
    except UnboundLocalError:
      # This test fails due to translation errors
      pass
