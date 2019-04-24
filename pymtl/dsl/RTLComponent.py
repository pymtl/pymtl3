#=========================================================================
# RTLComponent.py
#=========================================================================
# Currently we add reset and clk signal on top of ComponentLevel3 in the
# kernel. Later this might be handled by a PyMTL pass.
#
# Author : Shunning Jiang
# Date   : Jan 7, 2018

from pymtl.datatypes import Bits1
from ComponentLevel3 import ComponentLevel3
from Connectable import Connectable, Signal, InPort

import inspect, ast # for error message

class RTLComponent( ComponentLevel3 ):

  # Override
  def _construct( s ):
    """ We override _construct here to add clk/reset signals. I add signal
    declarations before constructing child components and bring up them
    to parent after construction of all children. """

    if not s._dsl.constructed:
      s.clk   = InPort( Bits1 )
      s.reset = InPort( Bits1 )

      kwargs = s._dsl.kwargs.copy()
      if "elaborate" in s._dsl.param_dict:
        kwargs.update( { x: y for x, y in s._dsl.param_dict[ "elaborate" ].iteritems()
                              if x } )
      if "construct" in s._dsl.param_dict:
        kwargs.update( { x: y for x, y in s._dsl.param_dict[ "construct" ].iteritems()
                              if x } )

      s.construct( *s._dsl.args, **kwargs )

      try:
        s.connect( s.clk, s.get_parent_object().clk )
        s.connect( s.reset, s.get_parent_object().reset )
      except AttributeError:
        pass

      if s._dsl.call_kwargs is not None: # s.a = A()( b = s.b )
        s._continue_call_connect()

      s._dsl.constructed = True

  def sim_reset( s ):
    assert s._dsl.elaborate_top is s # assert sim_reset is top

    s.reset = Bits1( 1 )
    s.tick() # This tick propagates the reset signal
    s.tick()
    s.reset = Bits1( 0 )

