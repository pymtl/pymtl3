"""
========================================================================
Component.py
========================================================================
Add clk/reset signals.

Author : Yanghui Ou
  Date : Apr 6, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits1

from .ComponentLevel7 import ComponentLevel7
from .Connectable import InPort


class Component( ComponentLevel7 ):

  # Override
  def _construct( s ):

    if not s._dsl.constructed:

      # clk and reset signals are added here.
      s.clk   = InPort( Bits1 )
      s.reset = InPort( Bits1 )

      # Merge the actual keyword args and those args set by set_parameter
      if s._dsl.param_tree.leaf is None:
        kwargs = s._dsl.kwargs
      else:
        kwargs = s._dsl.kwargs.copy()
        if "construct" in s._dsl.param_tree.leaf:
          more_args = s._dsl.param_tree.leaf[ "construct" ]
          kwargs.update( more_args )

      s._handle_decorated_methods()

      # We hook up the added clk and reset signals here.
      try:
        parent = s.get_parent_object()
        parent.connect( s.clk, parent.clk )
        parent.connect( s.reset, parent.reset )
      except AttributeError:
        pass

      # Same as parent class _construct
      s.construct( *s._dsl.args, **kwargs )

      if s._dsl.call_kwargs is not None: # s.a = A()( b = s.b )
        s._continue_call_connect()

      s._dsl.constructed = True

  def sim_reset( s ):
    assert s._dsl.elaborate_top is s # assert sim_reset is top

    s.reset = Bits1( 1 )
    s.tick() # This tick propagates the reset signal
    s.reset = Bits1( 0 )
    s.tick()
