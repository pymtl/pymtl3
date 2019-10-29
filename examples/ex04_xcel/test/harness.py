"""
=========================================================================
harness.py
=========================================================================
This files contains helper stuff for xcel tests.

Author : Shunning Jiang
  Date : June 15, 2019
"""

import struct

from examples.ex03_proc.NullXcel import NullXcelRTL
from examples.ex03_proc.tinyrv0_encoding import assemble
from pymtl3 import *
from pymtl3.passes import DynamicSim
from pymtl3.stdlib.cl.MemoryCL import MemoryCL
from pymtl3.stdlib.ifcs import mk_mem_msg
from pymtl3.stdlib.test import TestSinkCL, TestSrcCL

#=========================================================================
# TestHarness
#=========================================================================
# Use this with pytest parameterize so that the name of the function that
# generates the assembly test ends up as part of the actual test case
# name. Here is an example:
#
#  @pytest.mark.parametrize( "name,gen_test", [
#    asm_test( gen_basic_test  ),
#    asm_test( gen_bypass_test ),
#    asm_test( gen_value_test  ),
#  ])
#  def test( name, gen_test ):
#    run_test( ProcFL, gen_test )
#

def asm_test( func ):
  name = func.__name__
  if name.startswith("gen_"):
    name = name[4:]
  if name.endswith("_test"):
    name = name[:-5]

  return (name,func)

#=========================================================================
# TestHarness
#=========================================================================

class TestHarness(Component):

  #-----------------------------------------------------------------------
  # constructor
  #-----------------------------------------------------------------------

  def construct( s, proc_cls, xcel_cls, dump_vcd,
                 src_delay, sink_delay,
                 mem_stall_prob, mem_latency ):

    s.commit_inst = OutPort( Bits1 )
    req, resp = mk_mem_msg( 8, 32, 32 )

    s.src  = TestSrcCL ( Bits32, [], src_delay, src_delay  )
    s.sink = TestSinkCL( Bits32, [], sink_delay, sink_delay )

    s.dut  = ProcXcel( proc_cls, xcel_cls )( commit_inst = s.commit_inst )

    s.mem  = MemoryCL(2, latency = mem_latency)

    connect_pairs(
      # Processor <-> Proc/Mngr
      s.src.send, s.dut.mngr2proc,
      s.dut.proc2mngr, s.sink.recv,

      # Processor <-> Memory
      s.proc.imem,  s.mem.ifc[0],
      s.proc.dmem,  s.mem.ifc[1],
    )

  #-----------------------------------------------------------------------
  # load
  #-----------------------------------------------------------------------

  def load( self, mem_image ):

    # Iterate over the sections

    sections = mem_image.get_sections()
    for section in sections:

      # For .mngr2proc sections, copy section into mngr2proc src

      if section.name == ".mngr2proc":
        for i in range(0,len(section.data),4):
          bits = struct.unpack_from("<I",memoryview(section.data)[i:i+4])[0]
          # self.src.src.msgs.append( Bits32(bits) )
          self.src.msgs.append( Bits32(bits) )

      # For .proc2mngr sections, copy section into proc2mngr_ref src

      elif section.name == ".proc2mngr":
        for i in range(0,len(section.data),4):
          bits = struct.unpack_from("<I",memoryview(section.data)[i:i+4])[0]
          # self.sink.sink.msgs.append( Bits32(bits) )
          self.sink.msgs.append( Bits32(bits) )

      # For all other sections, simply copy them into the memory

      else:
        self.mem.write_mem( section.addr, section.data )

  #-----------------------------------------------------------------------
  # done
  #-----------------------------------------------------------------------

  def done( s ):
    return s.src.done() and s.sink.done()

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    return s.src.line_trace()  + " >" + \
           s.dut.line_trace() + \
           s.mem.line_trace()  + " > " + \
           s.sink.line_trace()

#=========================================================================
# run_test
#=========================================================================

def run_test( ProcModel, XcelModel, gen_test, dump_vcd=None,
              src_delay=0, sink_delay=0,
              mem_stall_prob=0, mem_latency=1,
              max_cycles=10000 ):

  # Instantiate and elaborate the model

  th = TestHarness( ProcModel, XcelModel, dump_vcd,
                    src_delay, sink_delay,
                    mem_stall_prob, mem_latency )

  th.elaborate()

  # Assemble the test program

  mem_image = assemble( gen_test() )

  # Load the program into the model

  th.load( mem_image )

  # Run the simulation

  th.apply( SimpleSim[1:] )
  th.sim_reset()

  print()

  T = 0
  while not th.done() and T < max_cycles:
    th.tick()
    print "{:3}: {}".format( T, th.line_trace() )
    T += 1

  # Force a test failure if we timed out

  assert T < max_cycles

  # Add a couple extra ticks so that the VCD dump is nicer

  th.tick()
  th.tick()
  th.tick()
