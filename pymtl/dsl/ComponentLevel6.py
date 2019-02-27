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
    # port = CalleePort( method ) 
    method._anti_name_conflict_rdy = guard
    return method 
  return real_guard

#-------------------------------------------------------------------------
# ComponentLevel6
#-------------------------------------------------------------------------

class ComponentLevel6( ComponentLevel5 ):

  # Override
  # def __new__( cls, *args, **kwargs ):
  #   inst = super( ComponentLevel6, cls ).__new__( cls, *args, **kwargs )

  #   def bind_method( meth ):
  #     def _meth( *args, **kwargs ):
  #       return meth( inst, *args, **kwargs )
  #     return _meth

  #   for x in dir( cls ):
  #     y = getattr( inst, x )
  #     if isinstance( y, CalleePort ):
  #       y.method = bind_method( y.method )
  #       y.rdy    = bind_method( y.rdy    )

  #   return inst
  
  # Override
  def _construct( s ):
    """ We override _construct here to finish the saved __call__
    connections right after constructing the model. The reason why we
    take this detour instead of connecting in __call__ directly, is that
    __call__ is done before setattr, and hence the child components don't
    know their name yet. _dsl.constructed is called in setattr after name
    tagging, so this is valid. (see NamedObject.py). """
    # print "" 
    # print "="*30
    # print "I AM CALLED!!!!"
    if not s._dsl.constructed:
      kwargs = s._dsl.kwargs.copy()
      if "elaborate" in s._dsl.param_dict:
        kwargs.update( { x: y for x, y in s._dsl.param_dict[ "elaborate" ].iteritems()
                              if x } )

      def bind_method( meth ):
        def _meth( *args, **kwargs ):
          return meth( s, *args, **kwargs )
        return _meth

      for x in dir( s ):
        y = getattr( s, x )
        # if isinstance( y, CalleePort ):
        #   y.method = bind_method( y.method )
        #   y.rdy    = bind_method( y.rdy    )

        # FIXME: This would break if the class has a memeber with 
        # attribute [_anti_name_conflict_rdy]
        if hasattr( y, '_anti_name_conflict_rdy' ):
          print "\nCreating MethodPort for ", y
          # port = CalleePort( bind_method( y ) )
          port = CalleePort( y )
          port.rdy = bind_method( y._anti_name_conflict_rdy )
          setattr( s, x, port )

      s.construct( *s._dsl.args, **kwargs )

      if s._dsl.call_kwargs is not None: # s.a = A()( b = s.b )
        s._continue_call_connect()

      s._dsl.constructed = True
