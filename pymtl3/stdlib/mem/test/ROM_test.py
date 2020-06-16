#=========================================================================
# ROM_test.py
#=========================================================================

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim

from ..ROM import ROM

def test_rom( cmdline_opts ):
  run_test_vector_sim( ROM(Bits32, 8, [8,7,6,5,4,3,2,1]), [
    ('addr', 'out*'),
    [ 1,      7 ],
    [ 2,      6 ],
  ], cmdline_opts )