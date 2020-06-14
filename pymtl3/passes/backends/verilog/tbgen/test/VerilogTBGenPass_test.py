#=========================================================================
# TBGenPass_test.py
#=========================================================================
# Author : Shunning Jiang
# Date   : Mar 18, 2020
"""Test if the imported object works correctly."""

import pytest

from pymtl3 import DefaultPassGroup
from pymtl3.datatypes import Bits1, Bits32, Bits48, Bits64, clog2, mk_bits
from pymtl3.dsl import Component, InPort, Interface, OutPort, Placeholder, connect
from pymtl3.passes.backends.verilog import *
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.stdlib.test_utils import TestVectorSimulator

from ...testcases import CaseConnectArrayBits32FooIfcComp


def local_do_test( _m ):
  _m.elaborate()
  _m.apply( VerilogPlaceholderPass() )
  m = VerilogTranslationImportPass()( _m )
  m.set_metadata( VerilogTBGenPass.case_name, '1234' )
  m.apply( VerilogTBGenPass() )
  sim = TestVectorSimulator( m, _m._tv, _m._tv_in, _m._tv_out )
  sim.run_test()

def test_normal_queue( do_test ):
  # Test a Placeholder with params in `construct`
  def tv_in( m, tv ):
    m.enq_en  @= tv[0]
    m.enq_msg @= tv[1]
    m.deq_en  @= tv[3]
  def tv_out( m, tv ):
    if tv[2] != '*': assert m.enq_rdy == tv[2]
    if tv[4] != '*': assert m.deq_rdy == tv[5]
    if tv[5] != '*': assert m.deq_msg == tv[4]
  class VQueue( Component, Placeholder ):
    def construct( s, data_width, num_entries, count_width ):
      s.count   =  OutPort( mk_bits( count_width )  )
      s.deq_en  =  InPort( Bits1  )
      s.deq_rdy = OutPort( Bits1  )
      s.deq_msg = OutPort( mk_bits( data_width ) )
      s.enq_en  =  InPort( Bits1  )
      s.enq_rdy = OutPort( Bits1  )
      s.enq_msg =  InPort( mk_bits( data_width ) )
      s.set_metadata( VerilogTranslationImportPass.enable, True )
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
  q._tv = tv
  q._tv_in = tv_in
  q._tv_out = tv_out
  do_test( q )

def test_CaseConnectArrayBits32FooIfcComp():
  case = CaseConnectArrayBits32FooIfcComp
  _m = case.DUT()
  _m.elaborate()
  _m.set_metadata( VerilogTranslationImportPass.enable, True )
  _m.apply( VerilogPlaceholderPass() )
  m = VerilogTranslationImportPass()( _m )
  m.set_metadata( VerilogTBGenPass.case_name, 'sb' )
  m.apply( VerilogTBGenPass() )
  sim = TestVectorSimulator( m, case.TV, case.TV_IN, case.TV_OUT )
  sim.run_test()
