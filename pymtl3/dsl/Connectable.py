"""
========================================================================
Connectable.py
========================================================================
Wires, ports, and interfaces, all inherited from Connectable.

Author : Shunning Jiang
Date   : Apr 16, 2018
"""
import types
from collections import deque

from pymtl3.datatypes import Bits, Bits1, is_bitstruct_class, mk_bits

from .errors import InvalidConnectionError
from .NamedObject import DSLMetadata, NamedObject
from .Placeholder import Placeholder


class Connectable:
  # I've given up maintaining adjacency list or disjoint set locally since
  # we need to easily disconnect things

  # Public API

  def get_host_component( s ):
    try:
      return s._dsl.host
    except AttributeError:
      try:
        host = s
        while not host.is_component():
          host = host.get_parent_object() # go to the component
        s._dsl.host = host
        return s._dsl.host
      except AttributeError:
        raise NotElaboratedError()

  def get_type( s ):
    try:
      return s._dsl.Type
    except AttriibuteError:
      raise NotElaboratedError()

  def __ifloordiv__( s, other ):
    # Currently this basically implements connect( s, other ), but to
    # avoid circular import, we replicate the implementation of connect.

    host, s_connectable, o_connectable = _connect_check( s, other, internal=False )

    # ifloordiv is the only entry point for connecting lambda
    if isinstance( other, types.LambdaType ):
      host._create_assign_lambda( s, other )
    else:
      host._connect_dispatch( s, other, s_connectable, o_connectable )

    return s

def _connect_check( o1, o2, internal ):
  """ Note that internal=False means we are just calling this API
      internally so that we don't connect other unconnectable fields by
      name in the interface."""

  o1_connectable = False
  o2_connectable = False

  # Get access to the top level component by identifying a connectable

  if isinstance( o1, Connectable ):
    o1_connectable = True
    top = o1._dsl.elaborate_top

  if isinstance( o2, Connectable ):
    o2_connectable = True
    o2_top = o2._dsl.elaborate_top

    if o1_connectable: assert o2._dsl.elaborate_top is top
    else:              top = o2_top

  if not o1_connectable and not o2_connectable:
    if internal:  return None, False, False

    raise InvalidConnectionError(f"class {type(o1)} and class {type(o2)} are both not connectable.\n"
                                 f"  (when connecting {o1!r} to {o2!r})")

  # Get the component from elaborate_stack
  try:
    host = NamedObject._elaborate_stack[-1]
  except AttributeError:
    raise InvalidConnectionError("Cannot call connect after elaboration.\n"
                                 "- Please use top.add_connection(...) API.")

  if isinstance( host, Placeholder ):
    raise InvalidPlaceholderError( "Cannot call connect {}"
          "in a placeholder component.".format( blk.__name__ ) )

  # Not sure if there is any case where we cannot get the top plus it's
  # not an internal connect call
  assert host is not None, "Please contact pymtl3 developer about this error."

  return host, o1_connectable, o2_connectable

# Checking if two slices/indices overlap
def _overlap( x, y ):
  if isinstance( x, int ):
    if isinstance( y, int ):  return x == y
    else:                     return y.start <= x < y.stop
  else: # x is slice
    if isinstance( y, int ):  return x.start <= y < x.stop
    else:
      if x.start <= y.start:  return y.start < x.stop
      else:                   return x.start < y.stop

# internal class for connecting signals and constants, not named object
class Const( Connectable ):
  def __init__( s, Type, v, parent ):
    s._dsl = DSLMetadata()
    s._dsl.Type = Type
    s._dsl.const = v
    s._dsl.parent_obj = parent

  def __repr__( s ):
    if s._dsl.Type is int:
      return f"int({s._dsl.const})"
    return f"{repr(s._dsl.const)}"

  def get_parent_object( s ):
    try:
      return s._dsl.parent_obj
    except AttributeError:
      raise NotElaboratedError()

  def is_component( s ):
    return False

  def is_signal( s ):
    return False

  def is_interface( s ):
    return False

class Signal( NamedObject, Connectable ):

  def __init__( s, Type=Bits1 ):
    if isinstance( Type, int ):
      Type = mk_bits(Type)
    else:
      assert isinstance( Type, type ) and ( issubclass( Type, Bits ) or is_bitstruct_class(Type) ), \
              f"RTL signal can only be of Bits type or bitstruct type, not {Type}.\n" \
              f"Note: an integer is also accepted: Wire(32) is equivalent to Wire(Bits32))"

    s._dsl.Type = Type
    s._dsl.type_instance = None

    s._dsl.slice  = None # None -- not a slice of some wire by default
    s._dsl.slices = {}
    s._dsl.top_level_signal = s

    s._dsl.needs_double_buffer = False

  def inverse( s ):
    pass

  def __getattr__( s, name ):
    if name[0] == '_': # private variables directly exit here
      return super().__getattribute__( name )

    if name not in s.__dict__:
      # Shunning: we move this from __init__ to here for on-demand type
      #           checking when the __getattr__ is indeed used.

      if s._dsl.type_instance is None:
        # Yanghui: this would break if another Type indeed has an nbits
        #          attribute.
        # try:  Type.nbits
        # except AttributeError: # not Bits type

        # FIXME: check if Type is actually a type?
        Type = s._dsl.Type
        if not issubclass( Type, Bits ):
          s._dsl.type_instance = Type()

      if s._dsl.type_instance is None:
        raise AttributeError("{} is not a signals with struct type, and has no attribute '{}'".format( s, name ))
      else:
        obj = getattr( s._dsl.type_instance, name )

      # We handle three cases here:
      # 1. If the object is list, we recursively generate lists of signals
      # 2. If the object is Bits, we use the Bits type
      # 3. Otherwise we just go for obj.__class__
      # Note that BitsN is a type now. 2 and 3 are actually unified.

      # Use deque to ensure BFS to ensure a[0] is accessed before a[1]
      Q = deque([ (obj, [], s, False) ])

      while Q:
        u, indices, parent, parent_is_list = Q.popleft()
        cls = u.__class__

        if cls is list:
          x = []
          for i, v in enumerate( u ):
            Q.append( ( v, indices+[i], x, True ) )

        else:
          x = s.__class__( cls )
          sd = s._dsl
          xd = x._dsl

          xd.type_instance = u
          xd.parent_obj = s
          xd.top_level_signal = sd.top_level_signal
          xd.elaborate_top = sd.elaborate_top

          xd.my_name     = name + "".join([ f"[{y}]" for y in indices ])
          xd.full_name   = f"{sd.full_name}.{name}"
          xd._my_name    = name
          xd._my_indices = indices

        if parent_is_list:
          parent.append( x )
        else:
          parent.__dict__[ name ] = x

    return s.__dict__[ name ]

  def __setitem__( s, idx, v ):
    pass # I have to override this to support a[0:1] |= b

  def __getitem__( s, idx ):
    if not issubclass( s._dsl.Type, Bits ):
      raise InvalidConnectionError( "We don't allow slicing on non-Bits signals." )

    # Turn index into a slice
    if isinstance( idx, int ):
      start, stop = idx, idx + 1
    elif isinstance( idx, slice ):
      start, stop = idx.start, idx.stop
    else: assert False, f"The slice {idx} is invalid"

    if s._dsl.slice is None:
      assert 0 <= start < stop <= s._dsl.Type.nbits, f"[{start}:{stop}] slice, check "\
                                                     f"0 <= {start} < {stop} <= {s._dsl.Type.nbits}"
      top_signal = s
    else:
      outer_start, outer_stop = s._dsl.slice.start, s._dsl.slice.stop
      # slicing over sliced signals
      assert 0 <= start < stop <= (outer_stop - outer_start), f"[{start}:{stop}] slice, check "\
                                                              f"0 <= {start} < {stop} <= {outer_stop - outer_start}"
      start += outer_start
      stop  += outer_start
      top_signal = s._dsl.parent_obj

    sl_tuple = (start, stop)
    if sl_tuple not in top_signal.__dict__:
      x = top_signal.__class__( mk_bits( stop - start ) )

      sd = top_signal._dsl
      xd = x._dsl
      xd.parent_obj = top_signal
      xd.top_level_signal = sd.top_level_signal
      xd.elaborate_top    = sd.elaborate_top

      sl_str = f"[{start}:{stop}]"

      xd.my_name   = f"{sd.my_name}{sl_str}"
      xd.full_name = f"{sd.full_name}{sl_str}"

      xd.slice       = slice( start, stop )
      top_signal.__dict__[ sl_tuple ] = sd.slices[ sl_tuple ] = x

    return top_signal.__dict__[ sl_tuple ]

  def default_value( s ):
    return s._dsl.Type()

  #-----------------------------------------------------------------------
  # Public APIs (only can be called after elaboration)
  #-----------------------------------------------------------------------

  def is_component( s ):
    return False

  def is_signal( s ):
    return True

  def is_input_value_port( s ):
    return False

  def is_output_value_port( s ):
    return False

  def is_wire( s ):
    return False

  def is_interface( s ):
    return False

  # Note: We currently define a leaf signal as int/Bits type signal, as
  #       opposed to BitStruct or normal Python object. A sliced signal is
  #       not a leaf signal. A non-leaf signal cannot be sliced or be a
  #       sliced signal.

  def is_leaf_signal( s ):
    return ( issubclass( s._dsl.Type, Bits ) and not s.is_sliced_signal() ) or \
           (s._dsl.Type is int)

  def get_leaf_signals( s ):
    if s.is_sliced_signal(): return []
    if s.is_leaf_signal():   return [ s ]

    leaf_signals = []
    def recursive_getattr( m, instance ):
      for x in instance.__dict__:
        signal = getattr( m, x )
        if signal.is_leaf_signal():
          leaf_signals.append( signal )
        else:
          recursive_getattr( signal, instance.__dict__[x] )

    # OK now it's not Bits or int, let's instantiate it if it's never
    # accessed
    if s._dsl.type_instance is None:
      s._dsl.type_instance = s._dsl.Type()
    recursive_getattr( s, s._dsl.type_instance )
    return leaf_signals

  def is_sliced_signal( s ):
    return s._dsl.slice is not None

  def is_top_level_signal( s ):
    return s._dsl.top_level_signal is s

  def get_top_level_signal( s ):
    top = s._dsl.top_level_signal
    return s if top is None else top

  def get_sibling_slices( s ):
    if s._dsl.slice:
      parent = s.get_parent_object()
      ret = list(parent._dsl.slices.values())
      ret.remove( s )
      return ret
    return []

  def slice_overlap( s, other ):
    assert other.get_parent_object() is s.get_parent_object(), \
      "You are only allowed to pass in a sibling signal."
    return _overlap( s._dsl.slice, other._dsl.slice )

# These three subtypes are for type checking purpose
class Wire( Signal ):
  def inverse( s ):
    return Wire( s._dsl.Type )

class InPort( Signal ):
  def inverse( s ):
    return OutPort( s._dsl.Type )
  def is_input_value_port( s ):
    return True

class OutPort( Signal ):
  def inverse( s ):
    return InPort( s._dsl.Type )
  def is_output_value_port( s ):
    return True

class Interface( NamedObject, Connectable ):

  def inverse( s ):
    s._dsl.inversed = True
    return s

  # Override
  # The same reason as __call__ connection. For s.x = A().inverse(),
  # inverse is executed before setattr, so we need to delay it ...

  def _construct( s ):
    if not s._dsl.constructed:
      s.construct( *s._dsl.args, **s._dsl.kwargs )

      inversed = False
      if hasattr( s._dsl, "inversed" ):
        inversed = s._dsl.inversed

      if inversed:
        for name, obj in s.__dict__.items():
          if name[0] != '_': # filter private variables
            if isinstance( obj, Signal ):
              setattr( s, name, obj.inverse() )
            else:
              setattr( s, name, obj )

      s._dsl.constructed = True

  # We move the connect functionality to Component
  # def connect()

  #-----------------------------------------------------------------------
  # Public APIs (only can be called after elaboration)
  #-----------------------------------------------------------------------

  def is_component( s ):
    return False

  def is_signal( s ):
    return False

  def is_interface( s ):
    return True

# CallerPort is connected an exterior method, called by the component's
# update block
# CalleePort exposes the method in the component to outside world

class MethodPort( NamedObject, Connectable ):

  def construct( self, *args, **kwargs ):
    raise NotImplementedError("You can only instantiate Caller/CalleePort.")

  def __call__( self, *args, **kwargs ):
    return self.method( *args, **kwargs )

  def is_component( s ):
    return False

  def is_signal( s ):
    return False

  def is_method_port( s ):
    return False

  def is_interface( s ):
    return False

  def in_non_blocking_interface( s ):
    return s._dsl.in_non_blocking_ifc

class CallerPort( MethodPort ):
  def construct( self, *, Type=None ): # keyword only!
    self.Type = Type
    self.method = None
    self._dsl.in_non_blocking_ifc = False

  def is_callee_port( s ):
    return False

  def is_caller_port( s ):
    return True

class CalleePort( MethodPort ):
  def construct( self, *, Type=None, method=None ): # keyword only!
    self.Type = Type
    self.method = method
    self._dsl.in_non_blocking_ifc = False

  def is_callee_port( s ):
    return True

  def is_caller_port( s ):
    return False

class CallIfcRTL( Interface ):

  def construct( s, *args, **kwargs ):
    raise NotImplementedError("You can only instantiate CallerIfcRTL/CalleeIfcRTL.")

  def __str__( s ):
    try:
      trace_len = s.trace_len
      trace_fmt = s.trace_fmt
    except AttributeError:
      trace_len = 0
      trace_fmt = ''

      if s.MsgType is not None:
        trace_len += len( f'{s.MsgType()}' ) + 2
        trace_fmt += "({s.msg})"

      if s.RetType is not None:
        trace_len += 1 + len( f'{s.RetType()}' )
        trace_fmt += "={s.ret}"

      if trace_len == 0:
        trace_len = 1
        trace_fmt = ' '

      s.trace_len = trace_len
      s.trace_fmt = trace_fmt

    if       s.en and not s.rdy:  return "X".ljust( trace_len ) # Not allowed
    elif not s.en and     s.rdy:  return " ".ljust( trace_len ) # Idle
    elif not s.en and not s.rdy:  return "#".ljust( trace_len ) # Stall
    return trace_fmt.format( **vars() ).ljust( trace_len )

class NonBlockingIfc( Interface ):
  def construct( s, *args, **kwargs ):
    raise NotImplementedError("You can only instantiate CallerIfcCL/CalleeIfcCL.")

  def __call__( s, *args, **kwargs ):
    return s.method( *args, **kwargs )

  def __str__( s ):
    return s._str_hook()

  def _str_hook( s ):
    return f"{s._dsl.my_name}"

class BlockingIfc( Interface ):
  def construct( s, *args, **kwargs ):
    raise NotImplementedError("You can only instantiate CallerIfcFL/CalleeIfcFL.")

  def __call__( s, *args, **kwargs ):
    return s.method( *args, **kwargs )

  def __str__( s ):
    return s._str_hook()

  def _str_hook( s ):
    return f"{s._dsl.my_name}"

#-------------------------------------------------------------------------
# First-class method-based interfaces
#-------------------------------------------------------------------------

class CalleeIfcRTL( CallIfcRTL ):

  def construct( s, *, en=None, rdy=None, MsgType=None, RetType=None ): # keyword only!
    s.MsgType = s.RetType = None

    if en is not None:
      s.en  = InPort ( Bits1 )

    if rdy is not None:
      s.rdy = OutPort( Bits1 )

    if MsgType is not None:
      s.msg = InPort ( MsgType )
      s.MsgType = MsgType

    if RetType is not None:
      s.ret = OutPort( RetType )
      s.RetType = RetType

class CallerIfcRTL( CallIfcRTL ):

  def construct( s, *, en=None, rdy=None, MsgType=None, RetType=None ): # keyword only!
    s.MsgType = s.RetType = None

    if en is not None:
      s.en  = OutPort( Bits1 )

    if rdy is not None:
      s.rdy = InPort( Bits1 )

    if MsgType is not None:
      s.msg = OutPort( MsgType )
      s.MsgType = MsgType

    if RetType is not None:
      s.ret = InPort( RetType )
      s.RetType = RetType

class CalleeIfcCL( NonBlockingIfc ):
  def construct( s, *, Type=None, method=None, rdy=None ): # keyword only!
    s.Type = Type
    s.method = CalleePort( Type=Type, method=method )
    s.rdy    = CalleePort( method=rdy )

    s.method._dsl.in_non_blocking_ifc = True
    s.rdy._dsl.in_non_blocking_ifc    = True

    s.method._dsl.is_rdy = False
    s.rdy._dsl.is_rdy    = True

class CallerIfcCL( NonBlockingIfc ):

  def construct( s, *, Type=None ): # keyword only!
    s.Type = Type

    s.method = CallerPort( Type=Type )
    s.rdy    = CallerPort()

    s.method._dsl.in_non_blocking_ifc = True
    s.rdy._dsl.in_non_blocking_ifc    = True

    s.method._dsl.is_rdy = False
    s.rdy._dsl.is_rdy    = True

class CalleeIfcFL( BlockingIfc ):

  def construct( s, *, Type=None, method=None ):
    s.Type   = Type
    s.method = CalleePort( method=method, Type=Type )

class CallerIfcFL( BlockingIfc ):

  def construct( s, *, Type=None ):
    s.Type   = Type
    s.method = CallerPort( Type=Type )
