"""
========================================================================
AddSimUtilFuncsPass.py
========================================================================

Author : Shunning Jiang
Date   : Jan 26, 2020
"""

from pymtl3.datatypes import b1
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.errors import PassOrderError


class AddSimUtilFuncsPass( BasePass ):
  def __init__( self, active_high=True ):
    assert active_high in [ True, False ]
    self.active_high = active_high

  def __call__( self, top ):
    if not hasattr( top, "tick" ):
      raise PassOrderError( "tick" )

    if hasattr(top, "sim_reset"):
      raise AttributeError( "Please modify the attribute top.sim_reset to "
                            "a different name.")
    if hasattr(top, "print_line_trace"):
      raise AttributeError( "Please modify the attribute top.print_line_trace to "
                            "a different name.")

    top.sim_reset = self.create_reset( top, self.active_high )
    top.print_line_trace = self.create_print_line_trace( top )

  @staticmethod
  # Simulation related APIs
  def create_reset( top, active_high ):
    def reset( print_line_trace=False ):
      if print_line_trace:
        print()
      top.reset = b1( active_high )
      top.tick() # Tick twice to propagate the reset signal
      if print_line_trace:
        print( f"{top.simulated_cycles:3}r {top.line_trace()}" )
      top.tick()
      top.reset = b1( not active_high )
    return reset

  @staticmethod
  # Simulation related APIs
  def create_print_line_trace( top ):
    def print_line_trace():
      print( f"{top.simulated_cycles:3}: {top.line_trace()}" )
    return print_line_trace
