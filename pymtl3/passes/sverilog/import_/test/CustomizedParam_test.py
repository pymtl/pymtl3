
from __future__ import absolute_import, division, print_function

import os

from pymtl3.datatypes import Bits1, Bits3, Bits32, clog2, mk_bits
from pymtl3.dsl import Component, InPort, OutPort, Placeholder
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog import ImportPass
from pymtl3.stdlib.test import TestVectorSimulator


def get_dir():
  return os.path.dirname(os.path.abspath(__file__))+os.path.sep

def local_do_test( _m ):
  _m.elaborate()
  m = ImportPass()( _m )
  sim = TestVectorSimulator( m, _m._tv, _m._tv_in, _m._tv_out )
  sim.run_test()

class VQueue( Placeholder, Component ):

  def construct( s, import_params ):
    count_nbits = clog2( import_params["num_entries"] + 1 )
    s.count   =  OutPort( mk_bits( count_nbits )  )

    s.deq_en  =  InPort( Bits1  )
    s.deq_rdy = OutPort( Bits1  )
    s.deq_msg = OutPort( Bits32 )

    s.enq_en  =  InPort( Bits1  )
    s.enq_rdy = OutPort( Bits1  )
    s.enq_msg =  InPort( Bits32 )

def test_q_1( do_test ):
  num_entries = 1
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
  q = VQueue( { "num_entries" : 1 } )
  q.sverilog_import = True
  q.sverilog_import_path = get_dir() + 'VQueue.sv'
  q.sverilog_params = {
    "data_width"  : 32,
    "num_entries" : num_entries,
    "count_width" : clog2(num_entries+1),
  }
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
  q._tv = test_vector
  q._tv_in = tv_in
  q._tv_out = tv_out
  do_test( q )
