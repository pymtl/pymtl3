"""
==========================================================================
 ChecksumRTL_test.py
==========================================================================
Test cases for CL checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.passes import DynamicSim
from pymtl3.passes.sverilog.translation.TranslationPass import TranslationPass
from pymtl3.stdlib.cl.queues import BypassQueueCL
from pymtl3.stdlib.test import TestSinkCL, TestSrcCL

from .ChecksumCL_test import ChecksumScycleCL_Tests as BaseCLTests
from .ChecksumCL_test import ChecksumScycleCLSrcSink_Tests as BaseSrcSinkTests
from .ChecksumCL_test import TestHarness
from .ChecksumFL import b128_to_words, checksum, words_to_b128
from .ChecksumRTL import ChecksumRTL

#-------------------------------------------------------------------------
# Wrap RTL checksum unit into a function
#-------------------------------------------------------------------------

def checksum_rtl( words ):
  bits_in = words_to_b128( words )

  dut = ChecksumRTL()
  dut.apply( DynamicSim )

  dut.sim_reset()
  dut.send.rdy = b1(1)
  while not dut.recv.rdy:
    dut.tick()

  dut.recv.en = b1(1)
  dut.recv.msg = bits_in
  dut.tick()

  while not dut.send.en:
    dut.tick()
  
  return dut.send.msg

#-------------------------------------------------------------------------
# Functionality test
#-------------------------------------------------------------------------

class ChecksumRTL_Tests( BaseCLTests ):
  
  def func_impl( s, words ):
    return checksum_rtl( words )

#-------------------------------------------------------------------------
# Src/sink based tests
#-------------------------------------------------------------------------

class ChecksumRTLSrcSink_Tests( BaseSrcSinkTests ):

  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumRTL
    cls.nstages = None

#-------------------------------------------------------------------------
# Translation (temporary)
#-------------------------------------------------------------------------

def test_translate_sv():
  dut = ChecksumRTL()
  dut.elaborate()
  dut.sverilog_translate = True
  dut.apply( TranslationPass() )
