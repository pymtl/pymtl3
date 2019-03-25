#=========================================================================
# ComponentLevel6.py
#=========================================================================
# Add method port decorator and clk/reset signals.
#
# Author : Yanghui Ou
#   Date : Feb 24, 2019

from pymtl.datatypes import Bits1
from ComponentLevel5 import ComponentLevel5
from Connectable import CalleePort, MethodGuard, InVPort

#-------------------------------------------------------------------------
# method_port decorator
#-------------------------------------------------------------------------

def method_port( guard = lambda : True ):
  def real_guard( method ):
    method._anti_name_conflict_rdy = guard
    return method
  return real_guard

#-------------------------------------------------------------------------
# ComponentLevel6
#-------------------------------------------------------------------------

class ComponentLevel6( ComponentLevel5 ):

  # Override
  def _construct( s ):
    """ We override _construct here to add method binding. Basically
    we do this after the class is constructed but before the construct()
    elaboration happens."""

    if not s._dsl.constructed:

      s.clk   = InVPort( Bits1 )
      s.reset = InVPort( Bits1 )

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
          port = CalleePort( y )
          # NOTE we are in NameObject._setattr_for_elaborate_, we need
          # to first setattr "port" to "s" then add "rdy" to "port"
          setattr( s, x, port )
          port.rdy = MethodGuard( bind_method( y._anti_name_conflict_rdy ) )

      # Same as parent class _construct

      s.construct( *s._dsl.args, **kwargs )

      try:
        s.connect( s.clk, s.get_parent_object().clk )
        s.connect( s.reset, s.get_parent_object().reset )
      except AttributeError:
        pass

      if s._dsl.call_kwargs is not None: # s.a = A()( b = s.b )
        s._continue_call_connect()

      s._dsl.constructed = True

  def sim_reset( s ):
    assert s._dsl.elaborate_top is s # assert sim_reset is top

    s.reset = Bits1( 1 )
    s.tick() # This tick propagates the reset signal
    s.tick()
    s.reset = Bits1( 0 )
