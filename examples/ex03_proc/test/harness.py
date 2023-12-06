"""
=========================================================================
harness.py
=========================================================================
Includes a test harness that composes a processor, src/sink, and test
memory, and a run_test function.

Author : Shunning Jiang
  Date : June 15, 2019
"""

import struct

from examples.ex03_proc.NullXcel import NullXcelRTL
from examples.ex03_proc.tinyrv0_encoding import assemble
from pymtl3 import *
from pymtl3.stdlib.mem import MemoryFL, mk_mem_msg
from pymtl3.stdlib.connects import connect_pairs
from pymtl3.stdlib.stream import StreamSinkFL, StreamSourceFL

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

  def construct( s, proc_cls, xcel_cls=NullXcelRTL,
                 src_delay=0, sink_delay=0,
                 mem_stall_prob=0, mem_latency=1 ):

    s.commit_inst = OutPort()
    req, resp = mk_mem_msg( 8, 32, 32 )

    s.src  = StreamSourceFL( Bits32, [], src_delay, src_delay )
    s.sink = StreamSinkFL( Bits32, [], sink_delay, sink_delay )
    s.proc = proc_cls()
    s.xcel = xcel_cls()

    s.mem  = MemoryFL(2, mem_ifc_dtypes = [mk_mem_msg(8,32,32), mk_mem_msg(8,32,32)],
                      stall_prob=mem_stall_prob, extra_latency = mem_latency)

    connect_pairs(
      s.proc.commit_inst, s.commit_inst,

      # Processor <-> Proc/Mngr
      s.src.ostream, s.proc.mngr2proc,
      s.proc.proc2mngr, s.sink.istream,

      # Processor <-> Memory
      s.proc.imem, s.mem.ifc[0],
      s.proc.dmem, s.mem.ifc[1],
    )

    connect( s.proc.xcel, s.xcel.xcel )

  #-----------------------------------------------------------------------
  # load
  #-----------------------------------------------------------------------

  def load( self, mem_image ):

    # Iterate over the sections

    sections = mem_image.get_sections()
    for section in sections:

      # For .mngr2proc sections, copy section into mngr2proc src

      if section.name == ".mngr2proc":
        self.src.msgs.extend(Bits32(bits[0]) for bits in struct.iter_unpack("<I", section.data))

      # For .proc2mngr sections, copy section into proc2mngr_ref src

      elif section.name == ".proc2mngr":
        self.sink.msgs.extend(Bits32(bits[0]) for bits in struct.iter_unpack("<I", section.data))

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
    return s.src.line_trace()  + " > " + \
           s.proc.line_trace() + " > " + \
           s.sink.line_trace()
