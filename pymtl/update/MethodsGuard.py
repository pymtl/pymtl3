#=========================================================================
# Methods.py
#=========================================================================
# At this level, we add the ability to add a rdy guard to method port

from MethodsConnection import MethodsConnection
from Connectable import MethodPort

def guard_rdy( cond ):
  def real_guard( method ):
    setattr( method, "guard", "rdy" ) # method.guard "points to" method.rdy
    setattr( method, "rdy", cond )
    return method
  return real_guard

guard = guard_rdy

class MethodsGuard( MethodsConnection ):

  # Override
  def __new__( cls, *args, **kwargs ):
    inst = super( MethodsGuard, cls ).__new__( cls, *args, **kwargs )

    def wrap_lambda( f ):
      def _f( *args, **kwargs ):
        return f( inst, *args, **kwargs )
      return _f

    for x in dir(cls):
      y = getattr(inst, x)
      # look for all guarded method
      if isinstance( y, MethodPort ) and hasattr( y._func, "guard" ):
        gname = getattr( y._func, "guard" )
        guard = getattr( y._func, gname )

        assert not hasattr( y, gname ), "what the hell?"
        setattr( y, gname, wrap_lambda( guard ) )

    return inst
