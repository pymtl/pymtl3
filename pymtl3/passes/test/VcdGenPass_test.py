#=========================================================================
# VcdGenPass_test.py
#=========================================================================
# A simple demo of how VCD generation pass is used in the simulation of
# a toy component.
#
# Author : Peitian Pan
# Date   : Aug 28, 2019

from pymtl3 import *

class Toy( Component ):
  """Toy adder component"""

  def construct( s ):
    # Interfaces
    s.in0 = InPort( Bits32 )
    s.in1 = InPort( Bits32 )
    s.out = OutPort( Bits32 )

    @s.update
    def add_upblk():
      # This update block models the behavior of a 32-bit adder
      s.out = s.in0 + s.in1

def test_toy():
  # Create a toy component and elaborate it
  dut = Toy()
  dut.elaborate()

  # Enable VCD dumping
  dut.dump_vcd = True

  # Tell VCD generation pass which file it should dump output to
  dut.vcd_file_name = "toy_vcd"

  # Setup the simulation
  dut.apply( SimulationPass )
  dut.sim_reset()

  # Test vector
  vector = [
    #  in0        in1       out
    b32(1),    b32(2),    b32(3),
    b32(-1),   b32(2),    b32(1),
    b32(42),   b32(2),    b32(44),
    b32(1),    b32(-2),   b32(-1),
    b32(42),   b32(-42),  b32(0),
  ]

  # Begin simulation
  for in0, in1, out in zip(vector[0::3], vector[1::3], vector[2::3]):
    dut.in0 = in0
    dut.in1 = in1
    dut.tick()
    assert dut.out == out
