#=========================================================================
# ROM_test.py
#=========================================================================

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim

from ..ROM import CombinationalROM, SequentialROM


def test_combinational_rom_rtl():
  run_test_vector_sim( CombinationalROM(Bits32, 8, [8,7,6,5,4,3,2,1], num_ports=2), [
    ('raddr[0]', 'rdata[0]*', 'raddr[1]', 'rdata[1]*'),
    [ 1,          7,           5,          3          ],
    [ 2,          6,           7,          1          ],
  ])

  run_test_vector_sim( CombinationalROM(Bits32, 8, [8,7,6,5,4,3,2,1], num_ports=2), [
    ('raddr[0]', 'rdata[0]*', 'raddr[1]', 'rdata[1]*'),
    [ 1,          7,           5,          3          ],
    [ 2,          6,           7,          1          ],
  ], {'dump_textwave':False, 'dump_vcd': 'test_rom', 'test_verilog': 'ones',
      'test_yosys_verilog': '', 'dump_vtb': ''} )


def test_sequential_rom_rtl():
  run_test_vector_sim( SequentialROM(Bits32, 8, [8,7,6,5,4,3,2,1], num_ports=2), [
    ('raddr[0]', 'rdata[0]*', 'raddr[1]', 'rdata[1]*'),
    [ 1,          '?',         5,          '?'        ],
    [ 2,          7,           7,          3          ],
    [ 0,          6,           0,          1          ],
  ])

  run_test_vector_sim( SequentialROM(Bits32, 8, [8,7,6,5,4,3,2,1], num_ports=2), [
    ('raddr[0]', 'rdata[0]*', 'raddr[1]', 'rdata[1]*'),
    [ 1,          '?',         5,          '?'        ],
    [ 2,          7,           7,          3          ],
    [ 0,          6,           0,          1          ],
  ], {'dump_textwave':False, 'dump_vcd': 'test_rom', 'test_verilog': 'ones',
      'test_yosys_verilog': '', 'dump_vtb': ''} )
