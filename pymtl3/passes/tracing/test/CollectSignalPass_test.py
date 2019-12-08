#=========================================================================
# CollectSignalPass_test.py
#=========================================================================
# A simple demo of how collect signal pass is used in the simulation of
# a toy component.
#
# Author : Kaishuo Cheng
# Date   : Oct 8th, 2019

from pymtl3.datatypes import Bits32, b32
from pymtl3.dsl import *
from pymtl3.passes import SimulationPass, TracingConfigs
from pymtl3.passes.PassGroups import SimulationPass


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

def process_binary(sig):
  """
  Returns int value from a signal in 32b form. Used for testing.
  Example: input: 0b00000000000000000000000000000000
           output: 0
  """
  tempint = int(sig[2:],2)
  if sig[2] == '1':
     #taking 2's complement.
     #leading 1 indicates a negative number
    return tempint -2 **32

  else:
    return tempint

def test_toy():
  # Create a toy component and elaborate it
  dut = Toy()

  # Turn on textwave
  dut.config_tracing = TracingConfigs( tracing='text_fancy' )

  dut.elaborate()

  # Setup the simulation
  dut.apply( SimulationPass() )
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

  testlist = [
  #in0
  [0,0,1,-1,42,1,42], #dut's reset is on for the first two cycles".

  #in1
  [0,0,2,2,2,-2,-42],

  #out
  [0,0,3,1,44,-1,0]
  ]
  # Begin simulation
  for in0, in1, out in zip(vector[0::3], vector[1::3], vector[2::3]):
    dut.in0 = in0
    dut.in1 = in1
    dut.eval_combinational()
    dut.tick()
    assert dut.out == out

  #test
  sig = dut._tracing.text_sigs
  siglist = ["s.in0","s.in1","s.out","s.clk","s.reset"]
  for i in siglist:
    assert i in sig,"signals not captured"

  print(sig)
  for i in range(3): # in0, in1, and out
    partsig = sig[ siglist[i] ]
    signal_length = len(partsig)
    assert signal_length >= 5,"missing some cycles of signals"

    for j in range(signal_length):
      assert testlist[i][j] == process_binary(partsig[j]),"collected wrong signals"

  print("All signals captured in top._tracing.text_sigs!")
