"""
========================================================================
ComponentLevel6.py
========================================================================
Add method port decorator.

Author : Yanghui Ou, Shunning Jiang
  Date : Feb 24, 2019
"""
from __future__ import absolute_import, division, print_function

from .ComponentLevel5 import ComponentLevel5
from .Connectable import CalleePort, CallerPort, Interface

#-------------------------------------------------------------------------
# non blocking interfaces and decorator
#-------------------------------------------------------------------------

class NonBlockingCalleeIfc( Interface ):
  def construct( s, Type=method=None, rdy=None ):
    s.method = CalleePort( method )
    setattr( s, name, CalleePort( rdy ) )
    s._dsl.rdy = getattr( s, name )

    s.method._dsl.is_rdy    = False
    s._dsl.rdy._dsl.is_rdy  = True

  def __call__( s, *args, **kwargs ):
    return s.method( *args, **kwargs )

  def get_rdy( s ):
    return s._dsl.rdy

class NonBlockingCallerIfc( Interface ):

  def construct( s, Type ):
    s.method = CallerPort( Type )
    setattr( s, name, CallerPort() )

  def __call__( s, *args, **kwargs ):
    return s.method( *args, **kwargs )

def non_blocking( method ):
  method._rdy_method = guard
  return method

#-------------------------------------------------------------------------
# ComponentLevel6
#-------------------------------------------------------------------------

class ComponentLevel6( ComponentLevel5 ):

  def _handle_decorated_methods( s ):
    super( ComponentLevel6, s )._handle_decorated_methods()

    # The following code handles guarded methods
    def bind_method( method ):
      def _method( *args, **kwargs ):
        return method( s, *args, **kwargs )
      return _method

    cls_dict = s.__class__.__dict__
    for x in cls_dict:
      method = getattr( s, x )
      # We identify guarded methods here
      if hasattr( method, "_rdy_method" ):
        guard    = method._rdy_method
        setattr( s, x, NonblockingCalleeIfc( method, bind_method( guard ) ) )

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

      s._handle_decorated_methods()

      # Same as parent class _construct
      s.construct( *s._dsl.args, **kwargs )

      if s._dsl.call_kwargs is not None: # s.a = A()( b = s.b )
        s._continue_call_connect()

      s._dsl.constructed = True
