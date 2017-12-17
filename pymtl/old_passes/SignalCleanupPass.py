#-------------------------------------------------------------------------
# SignalCleanupPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.model import NamedObject, Signal, Const
from pymtl.passes import BasePass

class SignalCleanupPass( BasePass ):

  def apply( self, m ):
    if not hasattr( m, "tick" ):
      raise PassOrderError( "tick" )

    self.cleanup_wires( m )

  def cleanup_wires( self, m ):

    # SORRY
    if isinstance( m, list ):
      for i, o in enumerate( m ):
        if   isinstance( o, Signal ):
          m[i] = o.default_value()
        elif isinstance( o, Const ):
          m[i] = o.const
        else:
          self.cleanup_wires( o )

    elif isinstance( m, NamedObject ):
      for name, obj in m.__dict__.iteritems():
        if ( isinstance( name, basestring ) and not name.startswith("_") ) \
          or isinstance( name, tuple ):
            if   isinstance( obj, Signal ):
              try:
                setattr( m, name, obj.default_value() )
              except Exception as err:
                err.message = repr(obj) + " -- " + err.message
                err.args = (err.message,)
                raise err
            elif isinstance( obj, Const ):
              setattr( m, name, obj.const )
            else:
              self.cleanup_wires( obj )
