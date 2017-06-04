#-------------------------------------------------------------------------
# SignalCleanupPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.components import NamedObject, Signal
from pymtl.passes import BasePass
from collections import deque

class SignalCleanupPass( BasePass ):
  def execute( self, m ):
    self.cleanup_wires( m )
    return m

  @staticmethod
  def cleanup_wires( m ):

    # SORRY
    if isinstance( m, list ) or isinstance( m, deque ):
      for i, o in enumerate( m ):
        if isinstance( o, Signal ):
          m[i] = o.default_value()
        else:
          SignalCleanupPass.cleanup_wires( o )

    elif isinstance( m, NamedObject ):
      for name, obj in m.object_list:
        if ( isinstance( name, basestring ) and not name.startswith("_") ) \
          or isinstance( name, tuple ):
            if isinstance( obj, Signal ):
              setattr( m, name, obj.default_value() )
            else:
              SignalCleanupPass.cleanup_wires( obj )
