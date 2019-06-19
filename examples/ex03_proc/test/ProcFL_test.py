"""
=========================================================================
 ProcFL_test.py
=========================================================================
 Includes a test harness that composes a processor, src/sink, and test
 memory, and a run_test function.

Author : Shunning Jiang, Yanghui Ou
  Date : June 12, 2019
"""
import pytest
import random
random.seed(0xdeadbeef)

from pymtl3  import *
from harness import *
from examples.ex03_proc.ProcFL import ProcFL
import inst_add
import inst_and
import inst_sll
import inst_srl
import inst_bne
import inst_addi
import inst_lw
import inst_sw
import inst_csr
import inst_xcel

#-------------------------------------------------------------------------
# ProcFL_Tests
#-------------------------------------------------------------------------
# We group all our test cases into a class so that we can easily reuse
# these test cases in our CL and RTL tests. We can simply inherit from
# this test class and overwrite the ProcType of the test class.

class ProcFL_Tests( object ):

  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcFL

  #-----------------------------------------------------------------------
  # add
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_add.gen_basic_test     ) ,
    asm_test( inst_add.gen_dest_dep_test  ) ,
    asm_test( inst_add.gen_src0_dep_test  ) ,
    asm_test( inst_add.gen_src1_dep_test  ) ,
    asm_test( inst_add.gen_srcs_dep_test  ) ,
    asm_test( inst_add.gen_srcs_dest_test ) ,
    asm_test( inst_add.gen_value_test     ) ,
    asm_test( inst_add.gen_random_test    ) ,
  ])
  def test_add( s, name, test, dump_vcd ):
    run_test( s.ProcType, test, dump_vcd )

  def test_add_rand_delays( s, dump_vcd ):
    run_test( s.ProcType, inst_add.gen_random_test, dump_vcd,
            src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

  #-----------------------------------------------------------------------
  # and
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_and.gen_basic_test     ) ,
    asm_test( inst_and.gen_dest_dep_test  ) ,
    asm_test( inst_and.gen_src0_dep_test  ) ,
    asm_test( inst_and.gen_src1_dep_test  ) ,
    asm_test( inst_and.gen_srcs_dep_test  ) ,
    asm_test( inst_and.gen_srcs_dest_test ) ,
    asm_test( inst_and.gen_value_test     ) ,
    asm_test( inst_and.gen_random_test    ) ,
  ])
  def test_and( s, name, test, dump_vcd ):
    run_test( s.ProcType, test, dump_vcd )

  def test_and_rand_delays( s, dump_vcd ):
    run_test( s.ProcType, inst_and.gen_random_test, dump_vcd,
              src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

  #-----------------------------------------------------------------------
  # sll
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_sll.gen_basic_test     ) ,
    asm_test( inst_sll.gen_random_test    ) ,
  ])
  def test_sll( s, name, test, dump_vcd ):
    run_test( s.ProcType, test, dump_vcd )

  def test_sll_rand_delays( s, dump_vcd ):
    run_test( s.ProcType, inst_sll.gen_random_test, dump_vcd,
              src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

  #-----------------------------------------------------------------------
  # srl
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_srl.gen_basic_test     ) ,
    asm_test( inst_srl.gen_random_test    ) ,
  ])
  def test_srl( s, name, test, dump_vcd ):
    run_test( s.ProcType, test, dump_vcd )

  def test_srl_rand_delays( s, dump_vcd ):
    run_test( s.ProcType, inst_srl.gen_random_test, dump_vcd,
              src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

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
  def test_bne( s, name, test, dump_vcd ):
    run_test( s.ProcType, test, dump_vcd )

  def test_bne_rand_delays( s, dump_vcd ):
    run_test( s.ProcType, inst_bne.gen_random_test, dump_vcd,
              src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

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
  def test_addi( s, name, test, dump_vcd ):
    run_test( s.ProcType, test, dump_vcd )

  def test_addi_rand_delays( s, dump_vcd ):
    run_test( s.ProcType, inst_addi.gen_random_test, dump_vcd,
              src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

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
  def test_lw( s, name, test, dump_vcd ):
    run_test( s.ProcType, test, dump_vcd )

  def test_lw_rand_delays( s, dump_vcd ):
    run_test( s.ProcType, inst_lw.gen_random_test, dump_vcd,
              src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

  #-----------------------------------------------------------------------
  # sw
  #-----------------------------------------------------------------------


  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_sw.gen_basic_test     ),
    asm_test( inst_sw.gen_random_test    ),
  ])
  def test_sw( s, name, test, dump_vcd ):
    run_test( s.ProcType, test, dump_vcd )

  def test_sw_rand_delays( s, dump_vcd ):
    run_test( s.ProcType, inst_sw.gen_random_test, dump_vcd,
              src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

  #-----------------------------------------------------------------------
  # csr
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_csr.gen_basic_test      ),
    asm_test( inst_csr.gen_bypass_test     ),
    asm_test( inst_csr.gen_value_test      ),
    asm_test( inst_csr.gen_random_test     ),
  ])
  def test_csr( s, name, test, dump_vcd ):
    run_test( s.ProcType, test, dump_vcd )

  def test_csr_rand_delays( s, dump_vcd ):
    run_test( s.ProcType, inst_csr.gen_random_test, dump_vcd,
              src_delay=3, sink_delay=10, mem_stall_prob=0.5, mem_latency=3 )

  #-----------------------------------------------------------------------
  # xcel
  #-----------------------------------------------------------------------

  @pytest.mark.parametrize( "name,test", [
    asm_test( inst_xcel.gen_basic_test ),
    asm_test( inst_xcel.gen_multiple_test ),
  ])
  def test_xcel( s, name, test, dump_vcd ):
    run_test( s.ProcType, test, dump_vcd )

  def test_xcel_rand_delays( s, dump_vcd ):
    run_test( s.ProcType, inst_xcel.gen_multiple_test, dump_vcd,
              src_delay=3, sink_delay=10, mem_stall_prob=0.5, mem_latency=3 )
