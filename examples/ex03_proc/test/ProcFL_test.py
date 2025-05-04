"""
=========================================================================
ProcRTL_test.py
=========================================================================
Includes test cases for the RTL TinyRV0 processor.

Author : Shunning Jiang, Yanghui Ou
  Date : June 12, 2019
"""
import random

import pytest

from examples.ex03_proc.ProcFL import ProcFL
from pymtl3 import *
from pymtl3.stdlib.test_utils import run_sim

from . import (
    inst_add,
    inst_addi,
    inst_and,
    inst_bne,
    inst_csr,
    inst_lw,
    inst_sll,
    inst_srl,
    inst_sw,
    inst_xcel,
)
from .harness import TestHarness, asm_test, assemble

random.seed(0xdeadbeef)

#-------------------------------------------------------------------------
# ProcFL_Tests
#-------------------------------------------------------------------------

@pytest.mark.usefixtures("cmdline_opts")
class ProcFL_Tests:

  # [setup_class] will be called by pytest before running all the tests in
  # the test class. Here we specify the type of the processor that is used
  # in all test cases. We can easily reuse all these test cases in simply
  # by creating a new test class that inherits from this class and
  # overwrite the setup_class to provide a different processor type.
  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcFL

  # [run_sim] is a helper function in the test suite that creates a
  # simulator and runs test. We can overwrite this function when
  # inheriting from the test class to apply different passes to the DUT.
  def run_sim( s, th, gen_test ):

    th.elaborate()

    # Assemble the program
    mem_image = assemble( gen_test() )

    # Load the program into memory
    th.load( mem_image )

    run_sim( th, s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # add
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_add.gen_add_basic_test ) ,
    asm_test( inst_add.gen_dest_dep_test  ) ,
    asm_test( inst_add.gen_src0_dep_test  ) ,
    asm_test( inst_add.gen_src1_dep_test  ) ,
    asm_test( inst_add.gen_srcs_dep_test  ) ,
    asm_test( inst_add.gen_srcs_dest_test ) ,
    asm_test( inst_add.gen_value_test     ) ,
    asm_test( inst_add.gen_random_test    ) ,
  ])
  def test_add( s, name, test ):
    th = TestHarness( s.ProcType )
    s.run_sim( th, test )

  def test_add_rand_delays( s ):
    th = TestHarness( s.ProcType, src_delay=3, sink_delay=14,
                      mem_stall_prob=0.5, mem_latency=3 )
    s.run_sim( th, inst_add.gen_random_test )

  #-----------------------------------------------------------------------
  # and
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_and.gen_and_basic_test ) ,
  ])
  def test_and( s, name, test ):
    th = TestHarness( s.ProcType )
    s.run_sim( th, test )

  #-----------------------------------------------------------------------
  # sll
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_sll.gen_basic_test     ) ,
    asm_test( inst_sll.gen_random_test    ) ,
  ])
  def test_sll( s, name, test ):
    th = TestHarness( s.ProcType )
    s.run_sim( th, test )

  def test_sll_rand_delays( s ):
    th = TestHarness( s.ProcType, src_delay=3, sink_delay=14,
                      mem_stall_prob=0.5, mem_latency=3 )
    s.run_sim( th, inst_sll.gen_random_test )

  #-----------------------------------------------------------------------
  # srl
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_srl.gen_basic_test     ) ,
    asm_test( inst_srl.gen_random_test    ) ,
  ])
  def test_srl( s, name, test ):
    th = TestHarness( s.ProcType )
    s.run_sim( th, test )

  def test_srl_rand_delays( s ):
    th = TestHarness( s.ProcType, src_delay=3, sink_delay=14,
                      mem_stall_prob=0.5, mem_latency=3 )
    s.run_sim( th, inst_srl.gen_random_test )

  #-----------------------------------------------------------------------
  # bne
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_bne.gen_basic_test             ),
    asm_test( inst_bne.gen_src0_dep_taken_test    ),
    asm_test( inst_bne.gen_src0_dep_nottaken_test ),
    asm_test( inst_bne.gen_src1_dep_taken_test    ),
    asm_test( inst_bne.gen_src1_dep_nottaken_test ),
    asm_test( inst_bne.gen_srcs_dep_taken_test    ),
    asm_test( inst_bne.gen_srcs_dep_nottaken_test ),
    asm_test( inst_bne.gen_src0_eq_src1_test      ),
    asm_test( inst_bne.gen_value_test             ),
    asm_test( inst_bne.gen_random_test            ),
  ])
  def test_bne( s, name, test ):
    th = TestHarness( s.ProcType )
    s.run_sim( th, test )

  def test_bne_rand_delays( s ):
    th = TestHarness( s.ProcType, src_delay=3, sink_delay=14,
                      mem_stall_prob=0.5, mem_latency=3 )
    s.run_sim( th, inst_bne.gen_random_test )

  #-------------------------------------------------------------------------
  # addi
  #-------------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_addi.gen_basic_test     ),
    asm_test( inst_addi.gen_dest_dep_test  ),
    asm_test( inst_addi.gen_src_dep_test   ),
    asm_test( inst_addi.gen_srcs_dest_test ),
    asm_test( inst_addi.gen_value_test     ),
    asm_test( inst_addi.gen_random_test    ),
  ])
  def test_addi( s, name, test ):
    th = TestHarness( s.ProcType )
    s.run_sim( th, test )

  def test_addi_rand_delays( s ):
    th = TestHarness( s.ProcType, src_delay=3, sink_delay=14,
                      mem_stall_prob=0.5, mem_latency=3 )
    s.run_sim( th, inst_addi.gen_random_test )

  #-----------------------------------------------------------------------
  # lw
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_lw.gen_basic_test     ),
    asm_test( inst_lw.gen_dest_dep_test  ),
    asm_test( inst_lw.gen_base_dep_test  ),
    asm_test( inst_lw.gen_srcs_dest_test ),
    asm_test( inst_lw.gen_value_test     ),
    asm_test( inst_lw.gen_random_test    ),
  ])
  def test_lw( s, name, test ):
    th = TestHarness( s.ProcType )
    s.run_sim( th, test )

  def test_lw_rand_delays( s ):
    th = TestHarness( s.ProcType, src_delay=3, sink_delay=14,
                      mem_stall_prob=0.5, mem_latency=3 )
    s.run_sim( th, inst_lw.gen_random_test )

  #-----------------------------------------------------------------------
  # sw
  #-----------------------------------------------------------------------


  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_sw.gen_basic_test     ),
    asm_test( inst_sw.gen_random_test    ),
  ])
  def test_sw( s, name, test ):
    th = TestHarness( s.ProcType )
    s.run_sim( th, test )

  def test_sw_rand_delays( s ):
    th = TestHarness( s.ProcType, src_delay=3, sink_delay=14,
                      mem_stall_prob=0.5, mem_latency=3 )
    s.run_sim( th, inst_sw.gen_random_test )

  #-----------------------------------------------------------------------
  # csr
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_csr.gen_basic_test      ),
    asm_test( inst_csr.gen_bypass_test     ),
    asm_test( inst_csr.gen_value_test      ),
    asm_test( inst_csr.gen_random_test     ),
  ])
  def test_csr( s, name, test ):
    th = TestHarness( s.ProcType )
    s.run_sim( th, test )

  def test_csr_rand_delays( s ):
    th = TestHarness( s.ProcType, src_delay=3, sink_delay=14,
                      mem_stall_prob=0.5, mem_latency=3 )
    s.run_sim( th, inst_csr.gen_random_test )

  #-----------------------------------------------------------------------
  # xcel
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_xcel.gen_basic_test ),
    asm_test( inst_xcel.gen_multiple_test ),
  ])
  def test_xcel( s, name, test ):
    th = TestHarness( s.ProcType )
    s.run_sim( th, test )

  def test_xcel_rand_delays( s ):
    th = TestHarness( s.ProcType, src_delay=3, sink_delay=14,
                      mem_stall_prob=0.5, mem_latency=3 )
    s.run_sim( th, inst_xcel.gen_multiple_test )
