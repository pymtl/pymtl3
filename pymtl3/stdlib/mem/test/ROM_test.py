#=========================================================================
# ROM_test.py
#=========================================================================

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim

from ..ROM import ROM

def test_rom():
  run_test_vector_sim( ROM(Bits32, 8, [8,7,6,5,4,3,2,1], num_ports=2), [
    ('raddr[0]', 'rdata[0]*', 'raddr[1]', 'rdata[1]*'),
    [ 1,          7,           5,          3          ],
    [ 2,          6,           7,          1          ],
  ])

  run_test_vector_sim( ROM(Bits32, 8, [8,7,6,5,4,3,2,1], num_ports=2), [
    ('raddr[0]', 'rdata[0]*', 'raddr[1]', 'rdata[1]*'),
    [ 1,          7,           5,          3          ],
    [ 2,          6,           7,          1          ],
  ], {'dump_vcd': 'test_rom', 'test_verilog': 'ones', 'dump_vtb': ''} )


