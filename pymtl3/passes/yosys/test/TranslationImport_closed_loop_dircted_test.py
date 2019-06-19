#=========================================================================
# TranslationImport_closed_loop_directed_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jun 5, 2019
"""Closed-loop test with SystemVerilog translation and import."""

from __future__ import absolute_import, division, print_function

from pymtl3.passes import DynamicSim
from pymtl3.passes.sverilog.test.TranslationImport_closed_loop_dircted_test import (
    test_bypass_queue as _bypass_queue,
)
from pymtl3.passes.sverilog.test.TranslationImport_closed_loop_dircted_test import (
    test_bypass_queue_stall as _bypass_queue_stall,
)
from pymtl3.passes.sverilog.test.TranslationImport_closed_loop_dircted_test import (
    test_normal_queue as _normal_queue,
)
from pymtl3.passes.sverilog.test.TranslationImport_closed_loop_dircted_test import (
    test_normal_queue_stall as _normal_queue_stall,
)
from pymtl3.passes.sverilog.test.TranslationImport_closed_loop_dircted_test import (
    test_pipe_queue as _pipe_queue,
)
from pymtl3.passes.sverilog.test.TranslationImport_closed_loop_dircted_test import (
    test_pipe_queue_stall as _pipe_queue_stall,
)
from pymtl3.passes.yosys import ImportPass, TranslationPass

#-------------------------------------------------------------------------
# Valrdy queue tests
#-------------------------------------------------------------------------

def run_sim( _th ):
  try:
    _th.elaborate()
    _th.q.yosys_translate = True
    _th.q.yosys_import = True
    _th.apply( TranslationPass() )
    th = ImportPass()( _th )
    th.apply( DynamicSim )

    print()
    cycle = 0
    th.sim_reset()
    while not th.done() and cycle < 1000:
      th.tick()
      print(th.line_trace())
      cycle += 1

    assert cycle < 1000

    th.tick()
    th.tick()
    th.tick()
  finally:
    try:
      th.q.finalize()
    except UnboundLocalError:
      # This test fails due to translation errors
      pass

def test_normal_queue():
  test_func = _normal_queue
  _run_test = test_func.__globals__['run_sim']
  test_func.__globals__['run_sim'] = run_sim
  try:
    test_func()
  finally:
    test_func.__globals__['run_sim'] = _run_test

def test_normal_queue_stall():
  test_func = _normal_queue_stall
  _run_test = test_func.__globals__['run_sim']
  test_func.__globals__['run_sim'] = run_sim
  try:
    test_func()
  finally:
    test_func.__globals__['run_sim'] = _run_test

def test_pipe_queue():
  test_func = _pipe_queue
  _run_test = test_func.__globals__['run_sim']
  test_func.__globals__['run_sim'] = run_sim
  try:
    test_func()
  finally:
    test_func.__globals__['run_sim'] = _run_test

def test_pipe_queue_stall():
  test_func = _pipe_queue_stall
  _run_test = test_func.__globals__['run_sim']
  test_func.__globals__['run_sim'] = run_sim
  try:
    test_func()
  finally:
    test_func.__globals__['run_sim'] = _run_test

def test_bypass_queue():
  test_func = _bypass_queue
  _run_test = test_func.__globals__['run_sim']
  test_func.__globals__['run_sim'] = run_sim
  try:
    test_func()
  finally:
    test_func.__globals__['run_sim'] = _run_test

def test_bypass_queue_stall():
  test_func = _bypass_queue_stall
  _run_test = test_func.__globals__['run_sim']
  test_func.__globals__['run_sim'] = run_sim
  try:
    test_func()
  finally:
    test_func.__globals__['run_sim'] = _run_test
