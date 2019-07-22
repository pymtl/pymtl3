"""
========================================================================
ComponentLevel6.py
========================================================================
Add method port decorator.

Author : Yanghui Ou, Shunning Jiang
  Date : Feb 24, 2019
"""
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
    super()._handle_decorated_methods()

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
