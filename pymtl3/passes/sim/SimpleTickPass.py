"""
========================================================================
SimpleTickPass.py
========================================================================
Generate a simple tick function (no Mamba techniques here)

Author : Shunning Jiang
Date   : Dec 26, 2018
"""
from pymtl3.dsl import MethodPort
from pymtl3.dsl.errors import UpblkCyclicError
from pymtl3.passes.BasePass import BasePass
from pymtl3.passes.errors import PassOrderError

# Shunning: We are aware of the problem that there may be multiple places
# that assembles the function for the user to tick the simulator.
# I think LLVM applies passes based on the order they are inserted to the
# pass manager. LLVM also has some local ordering mechanism to figure out
# the dependencies between passes. Currently we haven't got to the point
# where we have enough passes to manage, but we should keep this in mind.

class SimpleTickPass( BasePass ):

  @staticmethod
  def gen_tick_function( schedule ):
    def iterative():
      for blk in schedule:
        blk()
    return iterative
