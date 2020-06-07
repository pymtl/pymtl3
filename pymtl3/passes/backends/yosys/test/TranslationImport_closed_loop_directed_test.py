#=========================================================================
# TranslationImport_closed_loop_directed_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 5, 2019
"""Closed-loop test with SystemVerilog translation and import."""

from pymtl3.passes.backends.verilog.test.TranslationImport_closed_loop_directed_test import (
    _run_queue_test_replace_run_sim,
)
from pymtl3.passes.PassGroups import DefaultPassGroup
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

from ..YosysTranslationImportPass import YosysTranslationImportPass

#-------------------------------------------------------------------------
# Valrdy queue tests
#-------------------------------------------------------------------------

def yosys_run_sim( _th ):
  _th.elaborate()
  _th.q.set_metadata( YosysTranslationImportPass.enable, True )
  th = YosysTranslationImportPass()( _th )

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

def test_normal_queue():
  _run_queue_test_replace_run_sim( yosys_run_sim, _normal_queue )

def test_normal_queue_stall():
  _run_queue_test_replace_run_sim( yosys_run_sim, _normal_queue_stall )

def test_pipe_queue():
  _run_queue_test_replace_run_sim( yosys_run_sim, _pipe_queue )

def test_pipe_queue_stall():
  _run_queue_test_replace_run_sim( yosys_run_sim, _pipe_queue_stall )

def test_bypass_queue():
  _run_queue_test_replace_run_sim( yosys_run_sim, _bypass_queue )

def test_bypass_queue_stall():
  _run_queue_test_replace_run_sim( yosys_run_sim, _bypass_queue_stall )
