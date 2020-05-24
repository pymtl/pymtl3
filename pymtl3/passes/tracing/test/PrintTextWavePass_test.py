#=========================================================================
# PrintWavePass_test.py
#=========================================================================
# A simple demo of how PrintWavePass is used in the simulation of
# a toy component.
#
# Author : Kaishuo Cheng
# Date   : Oct 8th, 2019

import io
from contextlib import redirect_stdout

from pymtl3.datatypes import (
    Bits1,
    Bits16,
    Bits32,
    Bits128,
    b1,
    b16,
    b32,
    b128,
    bitstruct,
)
from pymtl3.dsl import *
from pymtl3.passes.errors import ModelTypeError
from pymtl3.passes.PassGroups import DefaultPassGroup

from ..PrintTextWavePass import PrintTextWavePass


def test_collect_signal():

  class Toy( Component ):
    """Toy adder component"""

    def construct( s ):
      # Interfaces
      s.in0 = InPort( Bits32 )
      s.in1 = InPort( Bits32 )
      s.out = OutPort( Bits32 )

      @update
      def add_upblk():
        # This update block models the behavior of a 32-bit adder
        s.out @= s.in0 + s.in1

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

  # Create a toy component and elaborate it
  dut = Toy()

  dut.elaborate()

  # Turn on textwave
  dut.set_metadata( PrintTextWavePass.enable, True )

  # Setup the simulation
  dut.apply( DefaultPassGroup() )
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
  [0,0,0,1,-1,42,1,42], #dut's reset is on for the first two cycles".

  #in1
  [0,0,0,2,2,2,-2,-42],

  #out
  [0,0,0,3,1,44,-1,0]
  ]
  # Begin simulation
  for in0, in1, out in zip(vector[0::3], vector[1::3], vector[2::3]):
    dut.in0 @= in0
    dut.in1 @= in1
    dut.sim_tick()
    assert dut.out == out

  #test
  sig = dut.get_metadata( PrintTextWavePass.textwave_dict )
  siglist = ["s.in0","s.in1","s.out","s.reset"]
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


def test_toy():
  class Toy( Component ):
    """Toy adder component"""

    def construct( s ):
      # Interfaces
      s.i = InPort( Bits32 )
      s.inlong = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.state = Wire(Bits1)
      @update
      def add_upblk():
        # This update block models the behavior of a 32-bit adder
        s.out @= s.i + s.inlong
        if s.out[3]:
          s.state @= s.state +b1(1)
        else:
          s.state @= b1(0)

  # Create a toy component and elaborate it
  dut = Toy()
  dut.set_metadata( PrintTextWavePass.enable, True )

  # Setup the simulation
  dut.apply( DefaultPassGroup() )
  dut.sim_reset()
  # Test vector
  vector = [
    #  i        inlong       out
    b32(1),    b32(2),    b32(3),
    b32(0),    b32(2),    b32(2),
    b32(0),    b32(2),    b32(2),
    b32(1),    b32(-2),   b32(-1),
    b32(1),    b32(-42),  b32(-41),
    b32(1),    b32(-4),   b32(-3),
    b32(1),    b32(2),    b32(3),
    b32(0),    b32(2),    b32(2),
    b32(1),    b32(2),    b32(3),
    b32(0),    b32(-5),   b32(-5),
  ]

  # Begin simulation
  for i, inlong, out in zip(vector[0::3], vector[1::3], vector[2::3]):
    dut.i @= i
    dut.inlong @= inlong
    dut.sim_tick()
    assert dut.out == out

  #print
  f = io.StringIO()
  dut.print_textwave()
  with redirect_stdout(f):
    dut.print_textwave()
  out = f.getvalue()
  for i in dut.get_metadata( PrintTextWavePass.textwave_dict ):
    dot = i.find(".")
    sliced = i[dot+1:]
    if sliced != "reset" and sliced != "clk":
      assert i[dot+1:] in out

def test_widetoy():
  class Toy( Component ):

    def construct( s ):
      # Interfaces
      s.i = InPort( Bits128 )
      s.inlong = InPort( Bits128 )
      s.out = OutPort( Bits128 )
      s.state = Wire(Bits1)
      @update
      def add_upblk():
        # This update block models the behavior of a 32-bit adder
        s.out @= s.i + s.inlong
        if s.out[3]:
          s.state @= s.state + b1(1)
        else:
          s.state @= b1(0)

  # Create a toy component and elaborate it
  dut = Toy()

  dut.set_metadata( PrintTextWavePass.enable, True )

  dut.elaborate()

  # Setup the simulation
  dut.apply( DefaultPassGroup() )
  dut.sim_reset()
  # Test vector
  vector = [
    #  i        inlong       out
    b128(0x1000000000000+1),    b128(2),    b128(0x1000000000000+3),
    b128(0x1000000000000+0),    b128(2),    b128(0x1000000000000+2),
    b128(0x1000000000000+0),    b128(2),    b128(0x1000000000000+2),
    b128(0x1000000000000+1),    b128(-2),   b128(0x1000000000000+-1),
    b128(0x1000000000000+1),    b128(-42),  b128(0x1000000000000+-41),
    b128(0x1000000000000+1),    b128(-4),   b128(0x1000000000000+-3),
    b128(0x1000000000000+1),    b128(2),    b128(0x1000000000000+3),
    b128(0x1000000000000+0),    b128(2),    b128(0x1000000000000+2),
    b128(0x1000000000000+1),    b128(2),    b128(0x1000000000000+3),
    b128(0x1000000000000+0),    b128(-5),   b128(0x1000000000000+-5),
  ]

  # Begin simulation
  for i, inlong, out in zip(vector[0::3], vector[1::3], vector[2::3]):
    dut.i @= i
    dut.inlong @= inlong
    dut.sim_tick()
    assert dut.out == out

  #print
  f = io.StringIO()
  dut.print_textwave()
  with redirect_stdout(f):
    dut.print_textwave()
  out = f.getvalue()
  for i in dut.get_metadata( PrintTextWavePass.textwave_dict ):
    dot = i.find(".")
    sliced = i[dot+1:]
    if sliced != "reset" and sliced != "clk":
      assert i[dot+1:] in out

def test_bitstruct():

  @bitstruct
  class XX:
    x: Bits16
    y: Bits16

  class Toy( Component ):
    def construct( s ):
      # Interfaces
      s.i = InPort( XX )
      s.inlong = InPort( Bits16 )
      s.out = OutPort( XX )
      s.state = Wire(Bits1)
      @update
      def add_upblk():
        # This update block models the behavior of a 32-bit adder
        s.out.x @= s.i.x + s.inlong
        s.out.y @= s.i.y + s.inlong
        if s.out.x[3]:
          s.state @= s.state +b1(1)
        else:
          s.state @= b1(0)

  # Create a toy component and elaborate it
  dut = Toy()

  dut.set_metadata( PrintTextWavePass.enable, True )

  dut.elaborate()

  # Setup the simulation
  dut.apply( DefaultPassGroup() )

  dut.sim_reset()
  # Test vector
  vector = [
    #  i        inlong       out
    XX(1,1),    b16(2),    XX(3,3),
    XX(0,0),    b16(2),    XX(2,2),
    XX(0,0),    b16(2),    XX(2,2),
    XX(1,1),    b16(-2),   XX(-1,-1),
    XX(1,1),    b16(-42),  XX(-41,-41),
    XX(1,1),    b16(-4),   XX(-3,-3),
    XX(1,1),    b16(2),    XX(3,3),
    XX(0,0),    b16(2),    XX(2,2),
    XX(1,1),    b16(2),    XX(3,3),
    XX(0,0),    b16(-5),   XX(-5,-5),
  ]

  # Begin simulation
  for i, inlong, out in zip(vector[0::3], vector[1::3], vector[2::3]):
    dut.i @= i
    dut.inlong @= inlong
    dut.sim_tick()
    assert dut.out == out

  #print
  f = io.StringIO()
  dut.print_textwave()
  with redirect_stdout(f):
    dut.print_textwave()
  out = f.getvalue()
  for i in dut.get_metadata( PrintTextWavePass.textwave_dict ):
    dot = i.find(".")
    sliced = i[dot+1:]
    if sliced != "reset" and sliced != "clk":
      assert i[dot+1:] in out
