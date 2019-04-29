from __future__ import absolute_import, print_function

import struct
from builtins import map

import pytest

from pclib.rtl import TestSinkEnRdy, TestSourceEnRdy
from pymtl import *

from .enrdy_queues import *

# =========================================================================
# enrdy_queues_test.py
# =========================================================================
#
# Author : Shunning Jiang
# Date   : Mar 9, 2018



# -------------------------------------------------------------------------
# TestHarness
# -------------------------------------------------------------------------


class TestHarness(Component):
    def construct(s, Type, q, src_msgs, sink_msgs, src_stall_prob=0, sink_stall_prob=0):

        # Instantiate models

        s.src = TestSourceEnRdy(Type, src_msgs, src_stall_prob)
        s.q = q
        s.sink = TestSinkEnRdy(Type, sink_msgs, sink_stall_prob)

        # Connect

        s.connect(s.src.out, s.q.enq)
        s.connect(s.sink.in_, s.q.deq)

    def done(s):
        return s.src.done() and s.sink.done()

    def line_trace(s):
        return s.src.line_trace() + " " + s.q.line_trace() + " " + s.sink.line_trace()


def run_sim(model):
    model.apply(SimpleSim)

    print()
    cycle = 0
    while not model.done() and cycle < 1000:
        model.tick()
        print(model.line_trace())
        cycle += 1

    assert cycle < 1000

    model.tick()
    model.tick()
    model.tick()


F = lambda x: Bits32(x)

req = list(map(F, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))
resp = list(map(F, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))


def test_normal_queue():
    run_sim(TestHarness(Bits32, NormalQueue1RTL(Bits32), req, resp))


def test_normal_queue_stall():
    run_sim(TestHarness(Bits32, NormalQueue1RTL(Bits32), req, resp, 0.5, 0.25))


def test_pipe_queue():
    run_sim(TestHarness(Bits32, PipeQueue1RTL(Bits32), req, resp))


def test_pipe_queue_stall():
    run_sim(TestHarness(Bits32, PipeQueue1RTL(Bits32), req, resp, 0.5, 0.25))


def test_bypass_queue():
    run_sim(TestHarness(Bits32, BypassQueue1RTL(Bits32), req, resp))


def test_bypass_queue_stall():
    run_sim(TestHarness(Bits32, BypassQueue1RTL(Bits32), req, resp, 0.5, 0.25))
