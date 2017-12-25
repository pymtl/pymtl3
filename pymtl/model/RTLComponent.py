#=========================================================================
# RTLComponent.py
#=========================================================================

from pymtl.datatypes import Bits1
from ComponentLevel3 import ComponentLevel3
from Connectable import Connectable, Signal, InVPort, OutVPort, Wire, Const, _overlap
from errors      import InvalidConnectionError, SignalTypeError, NoWriterError, MultiWriterError
from collections import defaultdict, deque

import inspect, ast # for error message

class RTLComponent( ComponentLevel3 ):

  def _construct( s ):
    if not s._constructed:
      s.clk   = InVPort( Bits1 )
      s.reset = InVPort( Bits1 )

      s.construct( *s._args, **s._kwargs )
      if hasattr( s, "_call_kwargs" ): # s.a = A()( b = s.b )
        s._continue_call_connect()
      s._constructed = True

  def sim_reset( s ):
    # TODO assert this is the top level

    s.reset = Bits1( 1 )
    s.tick() # This tick propagates the reset signal
    s.tick()
    s.reset = Bits1( 0 )

  def _bringup_reset_clk( s ):
    visited = set( [ id(s) ] )
    for obj in s._id_obj.values():
      if isinstance( obj, RTLComponent ):
        while id(obj) not in visited:
          visited.add( id(obj) )
          assert hasattr( obj, "_parent" )
          parent = obj._parent
          s.connect( obj._parent.reset, obj.reset )
          s.connect( obj._parent.clk, obj.clk )
          obj = parent
