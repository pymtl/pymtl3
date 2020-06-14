#=========================================================================
# TranslationImport_closed_loop_directed_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 5, 2019
"""Closed-loop test with SystemVerilog translation and import."""

from pymtl3.datatypes import Bits1, mk_bits
from pymtl3.passes.PassGroups import DefaultPassGroup
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.stdlib.queues.test.enrdy_queues_test import (
    test_bypass_queue as _bypass_queue,
)
from pymtl3.stdlib.queues.test.enrdy_queues_test import (
    test_bypass_queue_stall as _bypass_queue_stall,
)
from pymtl3.stdlib.queues.test.enrdy_queues_test import (
    test_normal_queue as _normal_queue,
)
from pymtl3.stdlib.queues.test.enrdy_queues_test import (
    test_normal_queue_stall as _normal_queue_stall,
)
from pymtl3.stdlib.queues.test.enrdy_queues_test import test_pipe_queue as _pipe_queue
from pymtl3.stdlib.queues.test.enrdy_queues_test import (
    test_pipe_queue_stall as _pipe_queue_stall,
)

from .. import VerilogTranslationImportPass
from ..util.test_utility import closed_loop_component_input_test

#-------------------------------------------------------------------------
# Valrdy queue tests
#-------------------------------------------------------------------------

def run_sim( _th ):
  _th.elaborate()
  _th.q.set_metadata( VerilogTranslationImportPass.enable, True )
  th = VerilogTranslationImportPass()( _th )

  try:
    th.apply( DefaultPassGroup() )
    th.sim_reset()

    while not th.done() and th.sim_cycle_count() < 1000:
      th.sim_tick()

    assert th.sim_cycle_count() < 1000

    th.sim_tick()
    th.sim_tick()
    th.sim_tick()
  finally:
    th.q.finalize()

def _run_queue_test_replace_run_sim( run_sim, test_func ):
  original_run_sim = test_func.__globals__['run_sim']
  test_func.__globals__['run_sim'] = run_sim
  try:
    test_func()
  finally:
    test_func.__globals__['run_sim'] = original_run_sim

def test_normal_queue():
  _run_queue_test_replace_run_sim( run_sim, _normal_queue )

def test_normal_queue_stall():
  _run_queue_test_replace_run_sim( run_sim, _normal_queue_stall )

def test_pipe_queue():
  _run_queue_test_replace_run_sim( run_sim, _pipe_queue )

def test_pipe_queue_stall():
  _run_queue_test_replace_run_sim( run_sim, _pipe_queue_stall )

def test_bypass_queue():
  _run_queue_test_replace_run_sim( run_sim, _bypass_queue )

def test_bypass_queue_stall():
  _run_queue_test_replace_run_sim( run_sim, _bypass_queue_stall )
