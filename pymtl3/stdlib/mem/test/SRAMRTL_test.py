#=========================================================================
# SRAMRTL_test.py
#=========================================================================

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim

from ..SRAMRTL import SRAM1rwRTL, SRAM1r1wRTL


def test_SRAM1rwRTL():
  run_test_vector_sim( SRAM1rwRTL( 32, 8 ), [
    ('addr', 'ren', 'rdata*', 'wen', 'wdata' ),
    [    1,     1,        0,     1,  0x1234  ],
    [    2,     0,        0,     1,  0x5678  ],
    [    1,     1,        0,     0,  0x5678  ],
    [    2,     1,   0x1234,     0,  0x5678  ],
    [    3,     0,   0x5678,     0,  0x5678  ],
  ])

  run_test_vector_sim( SRAM1rwRTL( 32, 8 ), [
    ('addr', 'ren', 'rdata*', 'wen', 'wdata' ),
    [    1,     1,        0,     1,  0x1234  ],
    [    2,     0,        0,     1,  0x5678  ],
    [    1,     1,        0,     0,  0x5678  ],
    [    2,     1,   0x1234,     0,  0x5678  ],
    [    3,     0,   0x5678,     0,  0x5678  ],
  ], {'dump_vcd': 'test_rom', 'test_verilog': 'ones', 'dump_vtb': ''} )


def test_SRAM1r1wRTL():
  run_test_vector_sim( SRAM1r1wRTL( 32, 128 ), [
    ('ren', 'raddr', 'rdata*', 'wen',  'waddr',  'wdata'    ),
    [   1,       1,      '?',     1,        1,   0x1234,    ],
    [   1,       1,      '?',     1,        2,   0x5678,    ],
    [   1,       2,   0x1234,     0,        0,   0x5678,    ],
    [   0,       0,   0x5678,     0,        0,   0x5678,    ],
  ])

  run_test_vector_sim( SRAM1r1wRTL( 32, 128 ), [
    ('ren', 'raddr', 'rdata*', 'wen',  'waddr',  'wdata'    ),
    [   1,       1,      '?',     1,        1,   0x1234,    ],
    [   1,       1,      '?',     1,        2,   0x5678,    ],
    [   1,       2,   0x1234,     0,        0,   0x5678,    ],
    [   0,       0,   0x5678,     0,        0,   0x5678,    ],
  ], {'dump_vcd': 'test_rom', 'test_verilog': 'ones', 'dump_vtb': ''} )


