#=========================================================================
# Component.py
#=========================================================================
# Add clk/reset signals.
#
# Author : Yanghui Ou
#   Date : Apr 6, 2019

from pymtl.datatypes import Bits1
from ComponentLevel6 import ComponentLevel6
from Connectable import InPort

class Component( ComponentLevel6 ):

  # Override
  def _construct( s ):

    if not s._dsl.constructed:

      s.clk   = InPort( Bits1 )
      s.reset = InPort( Bits1 )
      
      kwargs = s._dsl.kwargs.copy()
      if "elaborate" in s._dsl.param_dict:
        kwargs.update( { x: y for x, y in s._dsl.param_dict[ "elaborate" ].iteritems()
                              if x } )

      s._handle_guard_methods()

      try:
        s.connect( s.clk, s.get_parent_object().clk )
        s.connect( s.reset, s.get_parent_object().reset )
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
