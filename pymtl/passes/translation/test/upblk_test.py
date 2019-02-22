#=========================================================================
# upblk_test.py
#=========================================================================
# This file includes directed tests cases for the translation pass. Test
# cases are mainly simple PRTL models with complicated expressions insdie
# one upblk.
# 
# Author : Peitian Pan
# Date   : Feb 21, 2019

import pytest

from pymtl.passes.test                import run_translation_test
from pymtl.passes.rast.test.rast_test import *

def local_do_test( m ):
  run_translation_test( m, m._test_vector )

[ pytest.mark.skipif( True, reason='Array index out of range' )(x) for x in [
  test_for_basic
] ]
