#=========================================================================
# ComponentLevel6.py
#=========================================================================
# Add method port decorator.
#
# Author : Yanghui Ou
#   Date : Feb 24, 2019


from collections import defaultdict, deque

from NamedObject import NamedObject
from ComponentLevel1 import ComponentLevel1
from ComponentLevel2 import ComponentLevel2
from ComponentLevel3 import ComponentLevel3
from ComponentLevel4 import ComponentLevel4
from ComponentLevel5 import ComponentLevel5
from ConstraintTypes import U, M
from Connectable import Signal, MethodPort, CalleePort, CallerPort

#-------------------------------------------------------------------------
# method_port decorator
#-------------------------------------------------------------------------

def method_port( guard = lambda : True ):
  def real_guard( method ):
    print "adding %s to object ..." % method.__name__ 
    print method
    print "" 
    port = CalleePort( method ) 
    port.rdy = guard
    return port
  return real_guard

#-------------------------------------------------------------------------
# ComponentLevel6
#-------------------------------------------------------------------------

class ComponentLevel6( ComponentLevel5 ):

  # Override
  def __new__( cls, *args, **kwargs ):
    inst = super( ComponentLevel6, cls ).__new__( cls, *args, **kwargs )

    def bind_method( meth ):
      def _meth( *args, **kwargs ):
        return meth( inst, *args, **kwargs )
      return _meth

    for x in dir( cls ):
      y = getattr( inst, x )
      if isinstance( y, CalleePort ):
        y.method = bind_method( y.method )
        y.rdy    = bind_method( y.rdy    )

    return inst