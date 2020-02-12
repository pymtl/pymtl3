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
from pymtl3.passes import TracingConfigs
from pymtl3.passes.errors import ModelTypeError
from pymtl3.passes.PassGroups import SimulationPass


def test_toy():
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

  # Create a toy component and elaborate it
  dut = Toy()
  dut.config_tracing = TracingConfigs( tracing='text_ascii' )

  # Setup the simulation
  dut.apply( SimulationPass() )
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
    dut.i = i
    dut.inlong = inlong
    dut.eval_combinational()
    dut.tick()
    assert dut.out == out

  #print
  f = io.StringIO()
  dut.print_textwave()
  with redirect_stdout(f):
    dut.print_textwave()
  out = f.getvalue()
  for i in dut._tracing.text_sigs:
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
      @s.update
      def add_upblk():
        # This update block models the behavior of a 32-bit adder
        s.out = s.i + s.inlong
        if s.out[3] == "1":
          s.state = s.state +b1(1)
        else:
          s.state = b1(0)

  # Create a toy component and elaborate it
  dut = Toy()

  dut.config_tracing = TracingConfigs( tracing='text_fancy' )

  dut.elaborate()

  # Setup the simulation
  dut.apply( SimulationPass() )
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
    dut.i = i
    dut.inlong = inlong
    dut.eval_combinational()
    dut.tick()
    assert dut.out == out

  #print
  f = io.StringIO()
  dut.print_textwave()
  with redirect_stdout(f):
    dut.print_textwave()
  out = f.getvalue()
  for i in dut._tracing.text_sigs:
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
      @s.update
      def add_upblk():
        # This update block models the behavior of a 32-bit adder
        s.out.x = s.i.x + s.inlong
        s.out.y = s.i.y + s.inlong
        if s.out.x[3] == "1":
          s.state = s.state +b1(1)
        else:
          s.state = b1(0)

  # Create a toy component and elaborate it
  dut = Toy()

  dut.config_tracing = TracingConfigs( tracing='text_fancy' )

  dut.elaborate()

  # Setup the simulation
  dut.apply( SimulationPass() )

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
    dut.i = i
    dut.inlong = inlong
    dut.eval_combinational()
    dut.tick()
    assert dut.out == out

  #print
  f = io.StringIO()
  dut.print_textwave()
  with redirect_stdout(f):
    dut.print_textwave()
  out = f.getvalue()
  for i in dut._tracing.text_sigs:
    dot = i.find(".")
    sliced = i[dot+1:]
    if sliced != "reset" and sliced != "clk":
      assert i[dot+1:] in out
