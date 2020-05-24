"""
========================================================================
ComponentLevel7.py
========================================================================
Add functional-level blocking method decorator.

Author : Shunning Jiang
Date   : Jan 23, 2020
"""
from .ComponentLevel6 import ComponentLevel6
from .Connectable import CalleeIfcCL, CalleeIfcFL, CalleePort

#-------------------------------------------------------------------------
# method_port decorator
#-------------------------------------------------------------------------

def blocking( method ):
  method._blocking = True
  return method

#-------------------------------------------------------------------------
# ComponentLevel7
#-------------------------------------------------------------------------

class ComponentLevel7( ComponentLevel6 ):

  # override
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

      # We identify blocking methods here
      elif hasattr( method, "_blocking" ):
        setattr( s, x, CalleeIfcFL( method=method ) )
