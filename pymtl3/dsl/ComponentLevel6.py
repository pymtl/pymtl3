"""
========================================================================
ComponentLevel6.py
========================================================================
Add method port decorator.

Author : Yanghui Ou, Shunning Jiang
  Date : Jan 24, 2020
"""
from .ComponentLevel5 import ComponentLevel5
from .Connectable import CalleeIfcCL, CalleePort

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

  # Override
  def _handle_decorated_methods( s ):

    # The following code handles non-blocking methods
    def bind_method( method ):
      def _bound_method( *args, **kwargs ):
        return method( s, *args, **kwargs )
      return _bound_method

    for x in s.__class__.__dict__:
      method = getattr( s, x )

      # We identify decorated method port here
      if   hasattr( method, "_callee_port" ):
        setattr( s, x, CalleePort( method=method ) )

      # We identify non_blocking methods here
      elif hasattr( method, "_non_blocking_rdy" ):
        rdy  = method._non_blocking_rdy
        Type = method._non_blocking_type
        setattr( s, x, CalleeIfcCL( Type=Type, method=method, rdy=bind_method( rdy ) ) )
