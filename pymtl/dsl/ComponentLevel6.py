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
from .Connectable import CalleePort, CallerPort, NonBlockingCalleeIfc

#-------------------------------------------------------------------------
# non blocking decorator
#-------------------------------------------------------------------------

def non_blocking( rdy, Type=None ):
  def real_decorator( method ):
    method._non_blocking_rdy  = rdy
    method._non_blocking_type = Type
    return method
  return real_decorator

#-------------------------------------------------------------------------
# ComponentLevel6
#-------------------------------------------------------------------------

class ComponentLevel6( ComponentLevel5 ):

  def _handle_decorated_methods( s ):
    super( ComponentLevel6, s )._handle_decorated_methods()

    # The following code handles non-blocking methods
    def bind_method( method ):
      def _method( *args, **kwargs ):
        return method( s, *args, **kwargs )
      return _method

    cls_dict = s.__class__.__dict__
    for x in cls_dict:
      method = getattr( s, x )
      # We identify non_blocking methods here
      if hasattr( method, "_non_blocking_rdy" ):
        rdy  = method._non_blocking_rdy
        Type = method._non_blocking_type
        setattr( s, x, NonBlockingCalleeIfc( Type, method, bind_method( rdy ) ) )

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
