"""
========================================================================
CheckSignalNamePass_test.py
========================================================================

Author : Shunning Jiang
Date   : Dec 29, 2019
"""

from pymtl3.datatypes import Bits1
from pymtl3.dsl import *

from ..CheckSignalNamePass import CheckSignalNamePass


class Inner(Component):
  def construct( s, bad=True ):
    s.in_ = InPort(Bits1)

    if bad:
      s.Out = OutPort(Bits1)
      @update
      def up_bad():
        s.Out[0:1] @= s.in_ + 1

    else:
      s.out = OutPort(Bits1)
      @update
      def up_good():
        s.out[0:1] @= s.in_ + 1

def test_signal_name_default_function():

  class Top(Component):
    def construct( s ):
      s.inners = [ Inner( bad=(i%5==0) ) for i in range(10) ]

  top = Top()
  top.elaborate()
  top.apply( CheckSignalNamePass() )
  assert top.get_metadata( CheckSignalNamePass.result ) == [ top.inners[0].Out, top.inners[5].Out ]

def test_signal_name_custom_function():

  class Top(Component):
    def construct( s ):
      s.inners = [ Inner( bad=(i%5==0) ) for i in range(10) ]

  a = Top()
  a.elaborate()
  a.apply( CheckSignalNamePass(lambda x: x.get_field_name().isupper()) )
  # Every signal violated this UPPER check ...
  assert len(a.get_metadata( CheckSignalNamePass.result )) == 42 # 2 + 10 * (2+2)

  # Every signal instantiated in the inners array will have [] in its
  # full name.
  a.apply( CheckSignalNamePass(lambda x: '[' not in repr(x)) )
  assert len(a.get_metadata( CheckSignalNamePass.result )) == 40
