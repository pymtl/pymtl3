# =========================================================================
# UnrollTickPass.py
# =========================================================================
# Generate an unrolled tick function
#
# Author : Shunning Jiang
# Date   : Dec 26, 2018

from builtins import map
from builtins import range
import ast, py

from pymtl import *
from pymtl.passes import BasePass
from pymtl.passes.errors import PassOrderError


class UnrollTickPass(BasePass):
    def __call__(self, top):
        if not hasattr(top._sched, "schedule"):
            raise PassOrderError("schedule")

        schedule = top._sched.schedule

        # Berkin IlBeyi's recipe
        strs = list(
            map(
                "  update_blk{}() # {}".format,
                range(len(schedule)),
                [x.__name__ for x in schedule],
            )
        )
        gen_tick_src = """
        {}
        def tick_unroll():
          # The code below does the actual calling of update blocks.
          {}""".format(
            "; ".join(
                map("update_blk{0} = schedule[{0}]".format, range(len(schedule)))
            ),
            "\n          ".join(strs),
        )

        exec(py.code.Source(gen_tick_src).compile(), locals())

        top.tick = tick_unroll
