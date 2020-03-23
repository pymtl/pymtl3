from pymtl3 import Bits1
from pymtl3.passes import RedundantClkResetRemovalPass
from pymtl3.passes.testcases import (
    Bits16InOutPassThroughComp,
    CaseFlipFlopAdder,
    CaseSubCompAddComp,
    CaseSubCompFlipFlopAdder,
)
from pymtl3.stdlib.rtl import RegRst


def test_singleton_hierarhcy():
  m = RegRst( Bits1 )
  m.elaborate()
  m.apply( RedundantClkResetRemovalPass() )
  assert hasattr( m, 'clk' )
  assert hasattr( m, 'reset' )

def test_singleton_hierarhcy_no_reset():
  m = CaseFlipFlopAdder.DUT()
  m.elaborate()
  m.apply( RedundantClkResetRemovalPass() )
  assert hasattr( m, 'clk' )
  assert not hasattr( m, 'reset' )

def test_singleton_hierarhcy_no_clk_no_reset():
  m = Bits16InOutPassThroughComp()
  m.elaborate()
  m.apply( RedundantClkResetRemovalPass() )
  assert not hasattr( m, 'clk' )
  assert not hasattr( m, 'reset' )

def test_top_no_reset():
  m = CaseSubCompFlipFlopAdder.DUT()
  m.elaborate()
  m.apply( RedundantClkResetRemovalPass() )
  assert hasattr( m, 'clk' )
  assert not hasattr( m, 'reset' )
  assert hasattr( m.adder, 'clk' )
  assert not hasattr( m.adder, 'reset' )
