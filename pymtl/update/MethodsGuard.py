#=========================================================================
# Methods.py
#=========================================================================
# At this level, we add the ability to add a rdy guard to method port

from UpdatesExpl import verbose

from collections import defaultdict, deque
from PyMTLObject import PyMTLObject
from MethodsExpl import MethodsExpl
from MethodsConnection import MethodsConnection
from ASTHelper   import get_method_calls
from Connectable import MethodPort

class MethodsGuard( MethodsConnection ):

  # Override
  def __new__( cls, *args, **kwargs ):
    inst = super( MethodsGuard, cls ).__new__( cls, *args, **kwargs )

    def wrap_lambda( f ):
      def _f( *args, **kwargs ):
        return f( inst, *args, **kwargs )
      return _f

    for x in dir(cls):
      if x not in dir(MethodsGuard):
        y = getattr(inst, x)
        if isinstance( y, MethodPort ):
          func = y._func
          if hasattr( func, "guard" ):
            gname = getattr( func, "guard" )
            guard = getattr( func, gname )

            assert not hasattr( y, gname ), "what the hell?"
            setattr( y, gname, wrap_lambda( guard ) )

    return inst
