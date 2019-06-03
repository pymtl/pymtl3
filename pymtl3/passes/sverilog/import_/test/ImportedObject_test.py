#=========================================================================
# ImportedObject_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 2, 2019
"""Test if the imported object works correctly."""

from __future__ import absolute_import, division, print_function

import os

from pymtl3.datatypes import Bits1, Bits32
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.import_.ImportPass import get_imported_object
from pymtl3.stdlib.test import TestVectorSimulator


def get_dir():
  return os.path.dirname(os.path.abspath(__file__))+os.path.sep

def local_do_test( _m ):
  _m.elaborate()
  m = get_imported_object( _m )
  m.elaborate()
  sim = TestVectorSimulator( m, _m._test_vectors, _m._tv_in, _m._tv_out )

def test_reg( do_test ):
  def tv_in( m, test_vector ):
    m.d = Bits32( test_vector[0] )
  def tv_out( m, test_vector ):
    if test_vector[1] != '*':
      assert m.q == Bits32( test_vector[1] )
  class VReg( Component ):
    def construct( s ):
      s.q = OutPort( Bits32 )
      s.d = InPort( Bits32 )
  a = VReg()
  a._sverilog_import_path = get_dir()+'VReg.sv'
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
