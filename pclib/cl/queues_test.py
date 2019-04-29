from __future__ import absolute_import, print_function

import pytest

from pclib.test.test_sinks import TestSinkCL
from pclib.test.test_srcs import TestSrcCL
from pymtl import *
from pymtl.dsl.test.sim_utils import simple_sim_pass

from .queues import BypassQueueCL, NormalQueueCL, PipeQueueCL

# =========================================================================
# Tests for CL queues
# =========================================================================
#
# Author: Yanghui Ou
#   Date: Mar 20, 2019



# -------------------------------------------------------------------------
# TestHarness
# -------------------------------------------------------------------------


class TestHarness(Component):
    def construct(
        s,
        DutType,
        qsize,
        src_msgs,
        sink_msgs,
        src_initial,
        src_interval,
        sink_initial,
        sink_interval,
        arrival_time=None,
    ):

        s.src = TestSrcCL(src_msgs, src_initial, src_interval)
        s.dut = DutType(qsize)
        s.sink = TestSinkCL(sink_msgs, sink_initial, sink_interval, arrival_time)

        s.connect(s.src.send, s.dut.enq)

        @s.update
        def up_deq_send():
            if s.dut.deq.rdy() and s.sink.recv.rdy():
                s.sink.recv(s.dut.deq())

    def done(s):
        return s.src.done() and s.sink.done()

    def line_trace(s):
        return "{} ({}) {}".format(
            s.src.line_trace(), s.dut.line_trace(), s.sink.line_trace()
        )


# -------------------------------------------------------------------------
# run_sim
# -------------------------------------------------------------------------


def run_sim(th, max_cycles=100):

    # Create a simulator

    th.elaborate()
    th.apply(simple_sim_pass)

    # Run simulation

    print("")
    ncycles = 0
    print("{:2}:{}".format(ncycles, th.line_trace()))
    while not th.done() and ncycles < max_cycles:
        th.tick()
        ncycles += 1
        print("{:2}:{}".format(ncycles, th.line_trace()))

    # Check timeout

    assert ncycles < max_cycles

    th.tick()
    th.tick()
    th.tick()


# -------------------------------------------------------------------------
# Test cases
# -------------------------------------------------------------------------

test_msgs = [Bits16(0), Bits16(1), Bits16(2), Bits16(3)]

arrival_pipe = [2, 3, 4, 5]
arrival_bypass = [1, 2, 3, 4]
arrival_normal = [2, 4, 6, 8]


def test_pipe_simple():
    th = TestHarness(PipeQueueCL, 1, test_msgs, test_msgs, 0, 0, 0, 0, arrival_pipe)
    run_sim(th)


def test_bypass_simple():
    th = TestHarness(BypassQueueCL, 1, test_msgs, test_msgs, 0, 0, 0, 0, arrival_bypass)
    run_sim(th)


def test_normal_simple():
    th = TestHarness(NormalQueueCL, 1, test_msgs, test_msgs, 0, 0, 0, 0, arrival_normal)
    run_sim(th)


def test_normal2_simple():
    th = TestHarness(NormalQueueCL, 2, test_msgs, test_msgs, 0, 0, 0, 0, arrival_pipe)
    run_sim(th)


@pytest.mark.parametrize(
    (
        "QType",
        "qsize",
        "src_init_delay",
        "src_inter_delay",
        "sink_init_delay",
        "sink_inter_delay",
        "arrival_time",
    ),
    [
        (PipeQueueCL, 2, 1, 1, 0, 0, [3, 5, 7, 9]),
        (BypassQueueCL, 1, 0, 4, 3, 1, [3, 6, 11, 16]),
        (NormalQueueCL, 1, 0, 0, 5, 0, [5, 7, 9, 11]),
    ],
)
def test_delay(
    QType,
    qsize,
    src_init_delay,
    src_inter_delay,
    sink_init_delay,
    sink_inter_delay,
    arrival_time,
):
    th = TestHarness(
        QType,
        qsize,
        test_msgs,
        test_msgs,
        src_init_delay,
        src_inter_delay,
        sink_init_delay,
        sink_inter_delay,
        arrival_time,
    )
    run_sim(th)
