from __future__ import absolute_import, print_function

import random
import struct
from builtins import range, zip

import pytest

from pclib.ifcs import MemMsgType, mk_mem_msg, mk_mem_req_msg, mk_mem_resp_msg
from pclib.rtl import TestSinkValRdy, TestSourceValRdy
from pclib.test import mk_test_case_table
from pymtl import *

from .TestMemory import TestMemoryRTL

# =========================================================================
# TestMemory_test.py
# =========================================================================



# -------------------------------------------------------------------------
# TestHarness
# -------------------------------------------------------------------------


class TestHarness(Component):
    def construct(
        s, nports, src_msgs, sink_msgs, stall_prob, latency, src_delay, sink_delay
    ):

        # Message type

        ReqType, RespType = mk_mem_msg(8, 32, 32)

        # Instantiate models

        s.srcs = [TestSourceValRdy(ReqType, src_msgs[i]) for i in range(nports)]

        s.mem = TestMemoryRTL(nports, [ReqType] * nports, [RespType] * nports)

        s.sinks = [TestSinkValRdy(RespType, sink_msgs[i]) for i in range(nports)]

        # Connect

        for i in range(nports):
            s.connect(s.srcs[i].out, s.mem.reqs[i])
            s.connect(s.sinks[i].in_, s.mem.resps[i])

    def done(s):

        done_flag = 1
        for src, sink in zip(s.srcs, s.sinks):
            done_flag &= src.done() and sink.done()
        return done_flag

    def line_trace(s):
        return (
            s.srcs[0].line_trace()
            + " "
            + s.mem.line_trace()
            + " "
            + s.sinks[0].line_trace()
        )


# -------------------------------------------------------------------------
# make messages
# -------------------------------------------------------------------------

req_type_dict = {
    "rd": MemMsgType.READ,
    "wr": MemMsgType.WRITE,
    "ad": MemMsgType.AMO_ADD,
    "an": MemMsgType.AMO_AND,
    "or": MemMsgType.AMO_OR,
    "sw": MemMsgType.AMO_SWAP,
    "mn": MemMsgType.AMO_MIN,
}

resp_type_dict = {
    "rd": MemMsgType.READ,
    "wr": MemMsgType.WRITE,
    "ad": MemMsgType.AMO_ADD,
    "an": MemMsgType.AMO_AND,
    "or": MemMsgType.AMO_OR,
    "sw": MemMsgType.AMO_SWAP,
    "mn": MemMsgType.AMO_MIN,
}


def req(type_, opaque, addr, len, data):
    ReqType = mk_mem_req_msg(8, 32, 32)
    return ReqType(req_type_dict[type_], opaque, addr, len, data)


def resp(type_, opaque, len, data):
    RespType = mk_mem_resp_msg(8, 32)
    return RespType(resp_type_dict[type_], opaque, 0, len, data)


# ----------------------------------------------------------------------
# Test Case: basic
# ----------------------------------------------------------------------


def basic_msgs(base_addr):
    return [
        req("wr", 0x0, base_addr, 0, 0xDEADBEEF),
        resp("wr", 0x0, 0, 0),
        req("rd", 0x1, base_addr, 0, 0),
        resp("rd", 0x1, 0, 0xDEADBEEF),
    ]


# ----------------------------------------------------------------------
# Test Case: stream
# ----------------------------------------------------------------------


def stream_msgs(base_addr):

    msgs = []
    for i in range(20):
        msgs.extend(
            [
                req("wr", i, base_addr + 4 * i, 0, i),
                resp("wr", i, 0, 0),
                req("rd", i, base_addr + 4 * i, 0, 0),
                resp("rd", i, 0, i),
            ]
        )

    return msgs


# ----------------------------------------------------------------------
# Test Case: subword reads
# ----------------------------------------------------------------------


def subword_rd_msgs(base_addr):
    return [
        req("wr", 0x0, base_addr + 0, 0, 0xDEADBEEF),
        resp("wr", 0x0, 0, 0),
        req("rd", 0x1, base_addr + 0, 1, 0),
        resp("rd", 0x1, 1, 0x000000EF),
        req("rd", 0x2, base_addr + 1, 1, 0),
        resp("rd", 0x2, 1, 0x000000BE),
        req("rd", 0x3, base_addr + 2, 1, 0),
        resp("rd", 0x3, 1, 0x000000AD),
        req("rd", 0x4, base_addr + 3, 1, 0),
        resp("rd", 0x4, 1, 0x000000DE),
        req("rd", 0x5, base_addr + 0, 2, 0),
        resp("rd", 0x5, 2, 0x0000BEEF),
        req("rd", 0x6, base_addr + 1, 2, 0),
        resp("rd", 0x6, 2, 0x0000ADBE),
        req("rd", 0x7, base_addr + 2, 2, 0),
        resp("rd", 0x7, 2, 0x0000DEAD),
        req("rd", 0x8, base_addr + 0, 3, 0),
        resp("rd", 0x8, 3, 0x00ADBEEF),
        req("rd", 0x9, base_addr + 1, 3, 0),
        resp("rd", 0x9, 3, 0x00DEADBE),
        req("rd", 0xA, base_addr + 0, 0, 0),
        resp("rd", 0xA, 0, 0xDEADBEEF),
    ]


# ----------------------------------------------------------------------
# Test Case: subword writes
# ----------------------------------------------------------------------


def subword_wr_msgs(base_addr):
    return [
        req("wr", 0x0, base_addr + 0, 1, 0x000000EF),
        resp("wr", 0x0, 1, 0),
        req("wr", 0x1, base_addr + 1, 1, 0x000000BE),
        resp("wr", 0x1, 1, 0),
        req("wr", 0x2, base_addr + 2, 1, 0x000000AD),
        resp("wr", 0x2, 1, 0),
        req("wr", 0x3, base_addr + 3, 1, 0x000000DE),
        resp("wr", 0x3, 1, 0),
        req("rd", 0x4, base_addr + 0, 0, 0),
        resp("rd", 0x4, 0, 0xDEADBEEF),
        req("wr", 0x5, base_addr + 0, 2, 0x0000ABCD),
        resp("wr", 0x5, 2, 0),
        req("wr", 0x6, base_addr + 2, 2, 0x0000EF01),
        resp("wr", 0x6, 2, 0),
        req("rd", 0x7, base_addr + 0, 0, 0),
        resp("rd", 0x7, 0, 0xEF01ABCD),
        req("wr", 0x8, base_addr + 1, 2, 0x00002345),
        resp("wr", 0x8, 2, 0),
        req("rd", 0xA, base_addr + 0, 0, 0),
        resp("rd", 0xA, 0, 0xEF2345CD),
        req("wr", 0xB, base_addr + 0, 3, 0x00CAFE02),
        resp("wr", 0xB, 3, 0),
        req("rd", 0xC, base_addr + 0, 0, 0),
        resp("rd", 0xC, 0, 0xEFCAFE02),
    ]


# ----------------------------------------------------------------------
# Test Case: amos
# ----------------------------------------------------------------------


def amo_msgs(base_addr):
    return [
        # load some initial data
        req("wr", 0x0, base_addr, 0, 0x01234567),
        resp("wr", 0x0, 0, 0),
        req("wr", 0x0, base_addr + 4, 0, 0x98765432),
        resp("wr", 0x0, 0, 0),
        req("wr", 0x0, base_addr + 8, 0, 0x22002200),
        resp("wr", 0x0, 0, 0),
        req("wr", 0x0, base_addr + 12, 0, 0x00112233),
        resp("wr", 0x0, 0, 0),
        req("wr", 0x0, base_addr + 16, 0, 0x44556677),
        resp("wr", 0x0, 0, 0),
        req("wr", 0x0, base_addr + 20, 0, 0x01230123),
        resp("wr", 0x0, 0, 0),
        # amo.add
        req("ad", 0x1, base_addr, 0, 0x12345678),
        resp("ad", 0x1, 0, 0x01234567),
        req("rd", 0x2, base_addr, 0, 0),
        resp("rd", 0x2, 0, 0x13579BDF),
        # amo.and
        req("an", 0x3, base_addr + 4, 0, 0x23456789),
        resp("an", 0x3, 0, 0x98765432),
        req("rd", 0x4, base_addr + 4, 0, 0),
        resp("rd", 0x4, 0, 0x00444400),
        # amo.or
        req("or", 0x5, base_addr + 8, 0, 0x01230123),
        resp("or", 0x5, 0, 0x22002200),
        req("rd", 0x6, base_addr + 8, 0, 0),
        resp("rd", 0x6, 0, 0x23232323),
        # amo.xchg
        req("sw", 0x5, base_addr + 12, 0, 0xDEADBEEF),
        resp("sw", 0x5, 0, 0x00112233),
        req("rd", 0x6, base_addr + 12, 0, 0),
        resp("rd", 0x6, 0, 0xDEADBEEF),
        # amo.min -- mem is smaller
        req("mn", 0x7, base_addr + 16, 0, 0xCAFEBABE),
        resp("mn", 0x7, 0, 0x44556677),
        req("rd", 0x8, base_addr + 16, 0, 0),
        resp("rd", 0x8, 0, 0x44556677),
        # amo.min -- arg is smaller
        req("mn", 0x9, base_addr + 20, 0, 0x01201234),
        resp("mn", 0x9, 0, 0x01230123),
        req("rd", 0xA, base_addr + 20, 0, 0),
        resp("rd", 0xA, 0, 0x01201234),
    ]


# ----------------------------------------------------------------------
# Test Case: random
# ----------------------------------------------------------------------


def random_msgs(base_addr):

    rgen = random.Random()
    rgen.seed(0xA4E28CC2)

    vmem = [rgen.randint(0, 0xFFFFFFFF) for _ in range(20)]
    msgs = []

    for i in range(20):
        msgs.extend([req("wr", i, base_addr + 4 * i, 0, vmem[i]), resp("wr", i, 0, 0)])

    for i in range(20):
        idx = rgen.randint(0, 19)

        if rgen.randint(0, 1):

            correct_data = vmem[idx]
            msgs.extend(
                [
                    req("rd", i, base_addr + 4 * idx, 0, 0),
                    resp("rd", i, 0, correct_data),
                ]
            )

        else:

            new_data = rgen.randint(0, 0xFFFFFFFF)
            vmem[idx] = new_data
            msgs.extend(
                [req("wr", i, base_addr + 4 * idx, 0, new_data), resp("wr", i, 0, 0)]
            )

    return msgs


# -------------------------------------------------------------------------
# Test Case Table
# -------------------------------------------------------------------------

test_case_table = mk_test_case_table(
    [
        ("msg_func          stall lat src sink"),
        ["basic", basic_msgs, 0.0, 0, 0, 0],
        ["stream", stream_msgs, 0.0, 0, 0, 0],
        ["subword_rd", subword_rd_msgs, 0.0, 0, 0, 0],
        ["subword_wr", subword_wr_msgs, 0.0, 0, 0, 0],
        ["amo", amo_msgs, 0.0, 0, 0, 0],
        ["random", random_msgs, 0.0, 0, 0, 0],
        ["random_3x14", random_msgs, 0.0, 0, 3, 14],
        ["stream_stall0.5_lat0", stream_msgs, 0.5, 0, 0, 0],
        ["stream_stall0.0_lat4", stream_msgs, 0.0, 4, 0, 0],
        ["stream_stall0.5_lat4", stream_msgs, 0.5, 4, 0, 0],
        ["random_stall0.5_lat4_3x14", random_msgs, 0.5, 4, 3, 14],
    ]
)

# FIXME use new data types

# -------------------------------------------------------------------------
# Test cases for 1 port
# -------------------------------------------------------------------------


@pytest.mark.parametrize(**test_case_table)
def test_1port(test_params, dump_vcd):
    msgs = test_params.msg_func(0x1000)
    run_sim(
        TestHarness(
            1,
            [msgs[::2]],
            [msgs[1::2]],
            test_params.stall,
            test_params.lat,
            test_params.src,
            test_params.sink,
        ),
        dump_vcd,
    )


# -------------------------------------------------------------------------
# Test cases for 2 port
# -------------------------------------------------------------------------


@pytest.mark.parametrize(**test_case_table)
def test_2port(test_params, dump_vcd):
    msgs0 = test_params.msg_func(0x1000)
    msgs1 = test_params.msg_func(0x2000)
    run_sim(
        TestHarness(
            2,
            [msgs0[::2], msgs1[::2]],
            [msgs0[1::2], msgs1[1::2]],
            test_params.stall,
            test_params.lat,
            test_params.src,
            test_params.sink,
        ),
        dump_vcd,
    )


# -------------------------------------------------------------------------
# Test Read/Write Mem
# -------------------------------------------------------------------------


def test_read_write_mem(dump_vcd):

    rgen = random.Random()
    rgen.seed(0x05A3E95B)

    # Test data we want to write into memory

    data = [rgen.randrange(-(2 ** 31), 2 ** 31) for _ in range(20)]

    # Convert test data into byte array

    data_bytes = struct.pack("<{}i".format(len(data)), *data)

    # Create memory messages to read and verify memory contents

    msgs = []
    for i, item in enumerate(data):
        msgs.extend([req("rd", 0x1, 0x1000 + 4 * i, 0, 0), resp("rd", 0x1, 0, item)])

    # Create test harness with above memory messages

    th = TestHarness(1, [msgs[::2]], [msgs[1::2]], 0, 0, 0, 0)
    th.elaborate()

    # Write the data into the test memory

    th.mem.write_mem(0x1000, data_bytes)

    # Run the test

    run_sim(th, dump_vcd)

    # Read the data back out of the test memory

    result_bytes = th.mem.read_mem(0x1000, len(data_bytes))

    # Convert result bytes into list of ints

    result = list(struct.unpack("<{}i".format(len(data)), result_bytes))

    # Compare result to original data

    assert result == data


def run_sim(model, dump_vcd):
    model.apply(SimpleSim)
    print()
    while not model.done():
        model.tick()
        print(model.line_trace())

    model.tick()
    model.tick()
    model.tick()
