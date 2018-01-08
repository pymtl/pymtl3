#=========================================================================
# RTLComponent.py
#=========================================================================

from pymtl.datatypes import Bits1
from ComponentLevel3 import ComponentLevel3
from Connectable import Connectable, Signal, InVPort

import inspect, ast # for error message

class RTLComponent( ComponentLevel3 ):

  # Override
  def _construct( s ):
    """ We override _construct here to add clk/reset signals. I add signal
    declarations before constructing child components and bring up them
    to parent after construction of all children. """

    if not s._constructed:
      s.clk   = InVPort( Bits1 )
      s.reset = InVPort( Bits1 )

      kwargs = s._kwargs.copy()
      if "elaborate" in s._param_dict:
        kwargs.update( { x: y for x, y in s._param_dict[ "elaborate" ].iteritems()
                              if x } )

      if not kwargs: s.construct( *s._args )
      else:          s.construct( *s._args, **kwargs )

      try:
        s.connect( s.clk, s._parent_obj.clk )
        s.connect( s.reset, s._parent_obj.reset )
      except AttributeError:
        pass

      if s._call_kwargs is not None: # s.a = A()( b = s.b )
        s._continue_call_connect()

      s._constructed = True

  def sim_reset( s ):
    assert s._elaborate_top is s # assert sim_reset is top

    s.reset = Bits1( 1 )
    s.tick() # This tick propagates the reset signal
    s.tick()
    s.reset = Bits1( 0 )

