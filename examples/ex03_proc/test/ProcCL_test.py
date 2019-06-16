"""
=========================================================================
 ProcCL_test.py
=========================================================================
 Includes a test harness that composes a processor, src/sink, and test
 memory, and a run_test function.

Author : Shunning Jiang
  Date : June 12, 2019
"""
import pytest
import random
random.seed(0xdeadbeef)

from pymtl3  import *
from harness import *
from examples.ex03_proc.ProcCL import ProcCL

#-------------------------------------------------------------------------
# add
#-------------------------------------------------------------------------

import inst_add

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
def test_add( name, test, dump_vcd ):
  run_test( ProcCL, test, dump_vcd )

def test_add_rand_delays( dump_vcd ):
  run_test( ProcCL, inst_add.gen_random_test, dump_vcd,
            src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

#-------------------------------------------------------------------------
# and
#-------------------------------------------------------------------------

import inst_and

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
def test_and( name, test, dump_vcd ):
  run_test( ProcCL, test, dump_vcd )

def test_and_rand_delays( dump_vcd ):
  run_test( ProcCL, inst_and.gen_random_test, dump_vcd,
            src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

#-------------------------------------------------------------------------
# sll
#-------------------------------------------------------------------------

import inst_sll

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_sll.gen_basic_test     ) ,
  asm_test( inst_sll.gen_random_test    ) ,
])
def test_sll( name, test, dump_vcd ):
  run_test( ProcCL, test, dump_vcd )

def test_sll_rand_delays( dump_vcd ):
  run_test( ProcCL, inst_sll.gen_random_test, dump_vcd,
            src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

#-------------------------------------------------------------------------
# srl
#-------------------------------------------------------------------------

import inst_srl

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_srl.gen_basic_test     ) ,
  asm_test( inst_srl.gen_random_test    ) ,
])
def test_srl( name, test, dump_vcd ):
  run_test( ProcCL, test, dump_vcd )

def test_srl_rand_delays( dump_vcd ):
  run_test( ProcCL, inst_srl.gen_random_test, dump_vcd,
            src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

#-------------------------------------------------------------------------
# bne
#-------------------------------------------------------------------------

import inst_bne

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
def test_bne( name, test, dump_vcd ):
  run_test( ProcCL, test, dump_vcd )

def test_bne_rand_delays( dump_vcd ):
  run_test( ProcCL, inst_bne.gen_random_test, dump_vcd,
            src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3)

#-------------------------------------------------------------------------
# addi
#-------------------------------------------------------------------------

import inst_addi

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_addi.gen_basic_test     ) ,
  asm_test( inst_addi.gen_dest_dep_test  ) ,
  asm_test( inst_addi.gen_src_dep_test   ) ,
  asm_test( inst_addi.gen_srcs_dest_test ) ,
  asm_test( inst_addi.gen_value_test     ) ,
  asm_test( inst_addi.gen_random_test    ) ,
])
def test_addi( name, test, dump_vcd ):
  run_test( ProcCL, test, dump_vcd )

def test_addi_rand_delays( dump_vcd ):
  run_test( ProcCL, inst_addi.gen_random_test, dump_vcd,
            src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

#-------------------------------------------------------------------------
# lw
#-------------------------------------------------------------------------

import inst_lw

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_lw.gen_basic_test     ) ,
  asm_test( inst_lw.gen_dest_dep_test  ) ,
  asm_test( inst_lw.gen_base_dep_test  ) ,
  asm_test( inst_lw.gen_srcs_dest_test ) ,
  asm_test( inst_lw.gen_value_test     ) ,
  asm_test( inst_lw.gen_random_test    ) ,
])
def test_lw( name, test, dump_vcd ):
  run_test( ProcCL, test, dump_vcd )

def test_lw_rand_delays( dump_vcd ):
  run_test( ProcCL, inst_lw.gen_random_test, dump_vcd,
            src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

#-------------------------------------------------------------------------
# sw
#-------------------------------------------------------------------------

import inst_sw

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_sw.gen_basic_test     ),
  asm_test( inst_sw.gen_random_test    ),
])
def test_sw( name, test, dump_vcd ):
  run_test( ProcCL, test, dump_vcd )

def test_sw_rand_delays( dump_vcd ):
  run_test( ProcCL, inst_sw.gen_random_test, dump_vcd,
            src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3 )

#-------------------------------------------------------------------------
# csr
#-------------------------------------------------------------------------

import inst_csr

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_csr.gen_basic_test      ),
  asm_test( inst_csr.gen_bypass_test     ),
  asm_test( inst_csr.gen_value_test      ),
  asm_test( inst_csr.gen_random_test     ),
])
def test_csr( name, test, dump_vcd ):
  run_test( ProcCL, test, dump_vcd )

def test_csr_rand_delays( dump_vcd ):
  run_test( ProcCL, inst_csr.gen_random_test, dump_vcd,
            src_delay=3, sink_delay=10, mem_stall_prob=0.5, mem_latency=3)

import inst_xcel

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_xcel.gen_basic_test ),
  asm_test( inst_xcel.gen_multiple_test ),
])
def test_xcel( name, test, dump_vcd ):
  run_test( ProcCL, test, dump_vcd )

def test_xcel_rand_delays( dump_vcd ):
  run_test( ProcCL, inst_xcel.gen_multiple_test, dump_vcd,
            src_delay=3, sink_delay=10, mem_stall_prob=0.5, mem_latency=3)
