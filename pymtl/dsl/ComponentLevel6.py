#=========================================================================
# ComponentLevel6.py
#=========================================================================
# Add method port decorator.
#
# Author : Yanghui Ou
#   Date : Feb 24, 2019

from ComponentLevel5 import ComponentLevel5
from Connectable import CallerPort, CalleePort, Interface

#-------------------------------------------------------------------------
# method_port decorator
#-------------------------------------------------------------------------

def guarded_ifc( guard = lambda : True ):
  def real_guard( method ):
    method._anti_name_conflict_rdy = guard
    return method
  return real_guard

#-------------------------------------------------------------------------
# ComponentLevel6
#-------------------------------------------------------------------------

class GuardedIfc( Interface ):
  def __call__( s, *args, **kwargs ):
    return s.method( *args, **kwargs )

class GuardedCalleeIfc( GuardedIfc ):
  def construct( s, method=None, rdy=None ):
    s.method = CalleePort( method )
    s.rdy    = CalleePort( rdy )

class GuardedCallerIfc( GuardedIfc ):
  def construct( s ):
    s.method = CallerPort()
    s.rdy    = CallerPort()

class ComponentLevel6( ComponentLevel5 ):

  # Override
  def _construct( s ):
    """ We override _construct here to add method binding. Basically
    we do this after the class is constructed but before the construct()
    elaboration happens."""

    if not s._dsl.constructed:
      kwargs = s._dsl.kwargs.copy()
      if "elaborate" in s._dsl.param_dict:
        kwargs.update( { x: y for x, y in s._dsl.param_dict[ "elaborate" ].iteritems()
                              if x } )

      # The following code handles guarded methods
      def bind_method( method ):
        def _method( *args, **kwargs ):
          return method( s, *args, **kwargs )
        return _method

      for x in dir( s ):
        # This getattr will get the bounded method from ComponentLevel4
        y = getattr( s, x )

        # This would break if this _method_ has a member with
        # attribute [_anti_name_conflict_rdy]
        if hasattr( y, '_anti_name_conflict_rdy' ):
          ifc = GuardedCalleeIfc( y, bind_method( y._anti_name_conflict_rdy ) )
          # NOTE we are in NameObject._setattr_for_elaborate_, we need
          # to first setattr "port" to "s" then add "rdy" to "port"
          setattr( s, x, ifc )

      # Same as parent class _construct

      s.construct( *s._dsl.args, **kwargs )

      if s._dsl.call_kwargs is not None: # s.a = A()( b = s.b )
        s._continue_call_connect()

      s._dsl.constructed = True
