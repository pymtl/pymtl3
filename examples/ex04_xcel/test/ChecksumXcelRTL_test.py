"""
==========================================================================
 ChecksumXcelRTL_test.py
==========================================================================
Test cases for RTL checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *

from ..ChecksumXcelRTL import ChecksumXcelRTL
from .ChecksumXcelCL_test import ChecksumXcelCLSrcSink_Tests as BaseTests

# TODO: add wrap func test.
# TODO: add more comments.
class ChecksumXcelRTLSrcSink_Tests( BaseTests ):

  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumXcelRTL

  # TODO: comments.
  def run_sim( s, th, max_cycles=1000 ):

    # Check command line arguments for vcd dumping
    import sys
    if hasattr( sys, '_pymtl_dump_vcd' ):
      if sys._pymtl_dump_vcd:
        th.dump_vcd = True
        th.vcd_file_name = "ChecksumXcelRTL"

    # Create a simulator
    th.elaborate()
    th.apply( SimulationPass )
    ncycles = 0
    th.sim_reset()
    print( "" )

    # Tick the simulator
    print("{:3}: {}".format( ncycles, th.line_trace() ))
    while not th.done() and ncycles < max_cycles:
      th.tick()
      ncycles += 1
      print("{:3}: {}".format( ncycles, th.line_trace() ))

    # Check timeout
    assert ncycles < max_cycles

