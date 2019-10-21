#=========================================================================
# PrintWavePass_test.py
#=========================================================================
# A simple demo of how PrintWavePass is used in the simulation of
# a toy component.
#
# Author : Kaishuo Cheng
# Date   : Oct 8th, 2019

from pymtl3 import *


class Toy( Component ):
  """Toy adder component"""

  def construct( s ):
    # Interfaces
    s.i = InPort( Bits32 )
    s.inlong = InPort( Bits32 )
    s.out = OutPort( Bits32 )
    s.state = Wire(Bits1)
    @s.update
    def add_upblk():
      # This update block models the behavior of a 32-bit adder
      s.out = s.i + s.inlong
      if s.out[3] == "1":
          s.state = s.state +b1(1)
      else:
          s.state = b1(0)

def test_toy():
  # Create a toy component and elaborate it
  dut = Toy()
  dut.elaborate()

  # Setup the simulation
  dut.apply( SimulationPass )
  dut.sim_reset()
  # Test vector
  vector = [
    #  i        inlong       out
    b32(1),    b32(2),    b32(3),
    b32(0),   b32(2),    b32(2),
    b32(0),   b32(2),    b32(2),
    b32(1),    b32(-2),   b32(-1),
    b32(1),   b32(-42),  b32(-41),
    b32(1),   b32(-4),  b32(-3),
    b32(1),   b32(2),  b32(3),
    b32(0),   b32(2),  b32(2),
    b32(1),   b32(2),  b32(3),
    b32(0),   b32(-5),  b32(-5),
  ]

  # Begin simulation
  for i, inlong, out in zip(vector[0::3], vector[1::3], vector[2::3]):
    dut.i = i
    dut.inlong = inlong
    dut.tick()
    assert dut.out == out

  #print
  dut._print_wave(dut)
test_toy()
