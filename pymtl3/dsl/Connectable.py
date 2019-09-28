"""
========================================================================
Connectable.py
========================================================================
Wires, ports, and interfaces, all inherited from Connectable.

Author : Shunning Jiang
Date   : Apr 16, 2018
"""
from collections import deque
from typing import Generic, TypeVar

from pymtl3.datatypes import Bits, mk_bits, BitStruct

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

  def __ifloordiv__( s, other ):
    # Currently this basically implements connect( s, other ), but to
    # avoid circular import, we replicate the implementation of connect.

    host, s_connectable, o_connectable = _connect_check( s, other, internal=False )
    host._connect_dispatch( s, other, s_connectable, o_connectable )
    return s

def _connect_check( o1, o2, internal ):
  """ Note that internal=False means we are just calling this API
      internally so that we don't connect other unconnectable fields by
      name in the interface."""

  o1_connectable = False
  o2_connectable = False
  top = None

  # Get access to the top level component by identifying a connectable

  if isinstance( o1, Connectable ) and not isinstance( o1, Const ):
    o1_connectable = True
    top = o1._dsl.elaborate_top

  if isinstance( o2, Connectable ) and not isinstance( o2, Const ):
    o2_connectable = True
    o2_top = o2._dsl.elaborate_top

    if o1_connectable: assert o2._dsl.elaborate_top is top
    else:              top = o2_top

  if not o1_connectable and not o2_connectable:
    if internal:  return None, False, False

    raise InvalidConnectionError("class {} and class {} are both not connectable.\n"
                                  "  (when connecting {} to {})" \
        .format( type(o1), type(o2), repr(o1), repr(o2)) )

  # Get the component from elaborate_stack

  try:
    host = top._dsl.elaborate_stack[-1]
  except AttributeError:
    raise InvalidConnectionError("Cannot call connect after elaboration.\n"
                                 "- Please use top.add_connection(...) API.")

  if isinstance( host, Placeholder ):
    raise InvalidPlaceholderError( "Cannot call connect "
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

T_ConstDataType = TypeVar("T_ConstDataType")

class Const( Connectable, Generic[T_ConstDataType] ):
  # def __init__( s, Type, v, parent ):
  def __init__( s, *args ):
    s._dsl = DSLMetadata()
    if len(args) == 3:
      s._dsl.Type = args[0]
      s._dsl.const = args[1]
      s._dsl.parent_obj = args[2]

    elif len(args) <= 1:
      cls = s.__class__
      assert cls.Type is not None
      s._dsl.Type = cls.Type
      if len(args) == 0:
        s._dsl.const = 0
      else:
        s._dsl.const = args[0]
      s._dsl.parent_obj = None
      cls.Type = None

      # Add simulation support because Const[BitsN](value) might appear
      # in an upblk
      s.nbits = s._dsl.Type.nbits
      s.value = s._dsl.Type( s._dsl.const )

    else:
      assert False

  def __class_getitem__( cls, Type ):
    if isinstance( Type, tuple ):
      raise TypeError(f"{cls} expects exactly one data type!")
    cls.Type = Type

    # Call the [] method of parent class (i.e. Generic)
    return super(Const, cls).__class_getitem__( Type )

  def __repr__( s ):
    return "{}({})".format( str(s._dsl.Type.__name__), s._dsl.const )

  def get_parent_object( s ):
    try:
      return s._dsl.parent_obj
    except AttributeError:
      raise NotElaboratedError()

  def get_sibling_slices( s ):
    return []

  def is_component( s ):
    return False

  def is_signal( s ):
    return False

  def is_interface( s ):
    return False

  #--------------------------------------------------------
  # The same arithmetics as Bits
  #--------------------------------------------------------

  def __add__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) + int(other) )
    except: return Bits( self.nbits, int(self.value) + int(other) )

  def __radd__( self, other ):
    return self.__add__( other )

  def __sub__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) - int(other) )
    except: return Bits( self.nbits, int(self.value) - int(other) )

  def __rsub__( self, other ):
    return Bits( self.nbits, other ) - self

  def __mul__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) * int(other) )
    except: return Bits( self.nbits, int(self.value) * int(other) )

  def __rmul__( self, other ):
    return self.__mul__( other )

  def __and__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) & int(other) )
    except: return Bits( self.nbits, int(self.value) & int(other) )

  def __rand__( self, other ):
    return self.__and__( other )

  def __or__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) | int(other) )
    except: return Bits( self.nbits, int(self.value) | int(other) )

  def __ror__( self, other ):
    return self.__or__( other )

  def __xor__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) ^ int(other) )
    except: return Bits( self.nbits, int(self.value) ^ int(other) )

  def __rxor__( self, other ):
    return self.__xor__( other )

  def __div__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) / int(other) )
    except: return Bits( self.nbits, int(self.value) / int(other) )

  def __floordiv__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) / int(other) )
    except: return Bits( self.nbits, int(self.value) / int(other) )

  def __mod__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) % int(other) )
    except: return Bits( self.nbits, int(self.value) / int(other) )

  def __lshift__( self, other ):
    nb = int(self.nbits)
    # TODO this doesn't work perfectly. We need a really smart
    # optimization that avoids the guard totally
    if int(other) >= nb: return Bits( nb )
    return Bits( nb, int(self.value) << int(other) )

  def __rshift__( self, other ):
    return Bits( self.nbits, int(self.value) >> int(other) )

  def __int__( s ):
    return int(s.value)

  def __invert__( self ):
    return Bits( self.nbits, ~int(self.value) )

  def __getitem__( self, idx ):
    sv = int(self.value)

    if isinstance( idx, slice ):
      start, stop = int(idx.start), int(idx.stop)
      assert not idx.step and start < stop and start >= 0 and stop <= self.nbits, \
            "Invalid access: [{}:{}] in a Bits{} instance".format( start, stop, self.nbits )
      return Bits( stop-start, (sv & ((1 << stop) - 1)) >> start )

    i = int(idx)
    assert 0 <= i < self.nbits
    return Bits( 1, (sv >> i) & 1 )

  # Const values are mutable in upblks
  def __setitem__( self, idx, v ):
    sv = int(self.value)

    if isinstance( idx, slice ):
      start, stop = int(idx.start), int(idx.stop)
      assert not idx.step and start < stop and start >= 0 and stop <= self.nbits, \
            "Invalid access: [{}:{}] in a Bits{} instance".format( start, stop, self.nbits )

      self.value = (sv & (~((1 << stop) - (1 << start)))) | \
                   ((int(v) & ((1 << (stop - start)) - 1)) << start)
      return

    i = int(idx)
    assert 0 <= i < self.nbits
    self.value = (sv & ~(1 << i)) | ((int(v) & 1) << i)

  def __index__( self ):
    return int(self.value)

class Signal( NamedObject, Connectable ):

  def __init__( s, _Type = None ):
    # If necessary, extract the real type from __class_getitem__ aka []
    cls = s.__class__
    if _Type is None:
      if not hasattr(cls, "Type") or cls.Type is None:
        raise TypeError(f"Data type of {cls} cannot be None!")
      Type = cls.Type

      # Different signals might be parametrized with different types, so
      # we need to unset the Type field of the current class so that if
      # there were any unassigned data types, we will catch that instead
      # of using stale data types.
      cls.Type = None

    else:
      Type = _Type

    if isinstance( Type, int ):
      raise Exception("Use actual type instead of int (it is deprecated).")
    s._dsl.Type = Type
    s._dsl.type_instance = None

    s._dsl.slice  = None # None -- not a slice of some wire by default
    s._dsl.slices = {}
    s._dsl.top_level_signal = None

  def __class_getitem__( cls, Type ):
    if isinstance( Type, tuple ):
      raise TypeError(f"{cls} expects exactly one data type!")
    cls.Type = Type

    # Call the [] method of parent class (i.e. Generic)
    return super(Signal, cls).__class_getitem__( Type )

  def inverse( s ):
    pass

  def __getattr__( s, name ):
    if name.startswith("_"): # private variable
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

      Q = deque( [ (obj, [], s, False) ] )

      while Q:
        u, indices, parent, parent_is_list = Q.popleft()
        cls = u.__class__

        if cls is list:
          x = []
          for i, v in enumerate( u ):
            Q.append( ( v, indices+[i], x, True ) )

        else:
          x = s.__class__( cls )
          x._dsl.type_instance = u
          x._dsl.parent_obj = s
          x._dsl.top_level_signal = s._dsl.top_level_signal
          x._dsl.elaborate_top = s._dsl.elaborate_top

          x._dsl.my_name   = name + "".join([ "[{}]".format(y) for y in indices ])
          x._dsl.full_name = s._dsl.full_name + "." + x._dsl.my_name

        if parent_is_list:
          parent.append( x )
        else:
          parent.__dict__[ name ] = x

    return s.__dict__[ name ]

  def __setitem__( s, idx, v ):
    pass # I have to override this to support a[0:1] |= b

  def __getitem__( s, idx ):
    # Turn index into a slice
    if isinstance( idx, int ):
      sl = slice( idx, idx+1 )
    elif isinstance( idx, slice ):
      sl = idx
    else: assert False, "What the hell?"

    sl_tuple = (sl.start, sl.stop)

    if sl_tuple not in s.__dict__:
      x = s.__class__( mk_bits( sl.stop - sl.start) )
      x._dsl.parent_obj = s
      x._dsl.top_level_signal = s
      x._dsl.elaborate_top = s._dsl.elaborate_top

      sl_str = "[{}:{}]".format( sl.start, sl.stop )

      x._dsl.my_name   = s._dsl.my_name + sl_str
      x._dsl.full_name = s._dsl.full_name + sl_str

      x._dsl.slice       = sl
      s.__dict__[ sl_tuple ] = s._dsl.slices[ sl_tuple ] = x

    return s.__dict__[ sl_tuple ]

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
    return not s._dsl.slice is None

  def is_top_level_signal( s ):
    return s._dsl.top_level_signal is None

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

T_WireDataType = TypeVar("T_WireDataType")

# These three subtypes are for type checking purpose
class Wire( Signal, Generic[T_WireDataType] ):
  def inverse( s ):
    return Wire( s._dsl.Type )

T_InPortDataType = TypeVar("T_InPortDataType")

class InPort( Signal, Generic[T_InPortDataType] ):
  def inverse( s ):
    return OutPort( s._dsl.Type )
  def is_input_value_port( s ):
    return True

T_OutPortDataType = TypeVar("T_OutPortDataType")

class OutPort( Signal, Generic[T_OutPortDataType] ):
  def inverse( s ):
    return InPort( s._dsl.Type )
  def is_output_value_port( s ):
    return True

class Interface( NamedObject, Connectable ):

  def __init__( s, *args, **kwargs ):
    if hasattr( s.__class__, "__parameters__" ):
      # If necessary, extract the real type from __class_getitem__ aka []
      names     = list(map(lambda x: str(x)[1:], s.__class__.__parameters__))
      instances = s.__class__._rt_types
      assert len(names) == len(instances)
      # print(f"{names}, {instances}")
      s.construct.__globals__.update(
          {name:inst for name, inst in zip(names, instances)} )
      s.__class__._rt_types = None
      super(Interface, s).__init__()

    else:
      # super(Interface, s).__init__(*args, **kwargs)
      super(Interface, s).__init__()
      # try:
      # except TypeError:
      #   super(Interface, s).__init__()

  def __class_getitem__( cls, Types ):
    # Check if all the type instances are valid PyMTL types
    if not isinstance( Types, tuple ):
      Types = (Types,)
    assert all(issubclass(Type, (Bits, BitStruct)) for Type in Types)
    assert not hasattr(cls, "_rt_types") or cls._rt_types is None
    cls._rt_types = Types
    return super(Interface, cls).__class_getitem__( Types )

  def inverse( s ):
    s._dsl.inversed = True
    return s

  # Override
  # The same reason as __call__ connection. For s.x = A().inverse(),
  # inverse is executed before setattr, so we need to delay it ...

  def _construct( s ):
    if not s._dsl.constructed:
      s.construct( *s._dsl.args, **s._dsl.kwargs )
      # s.construct( s._dsl.Type )

      inversed = False
      if hasattr( s._dsl, "inversed" ):
        inversed = s._dsl.inversed

      if inversed:
        for name, obj in s.__dict__.items():
          if not name.startswith("_"):
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
  def construct( self, Type=None ):
    self.Type = Type
    self.method = None
    self._dsl.in_non_blocking_ifc = False

  def is_callee_port( s ):
    return False

  def is_caller_port( s ):
    return True

class CalleePort( MethodPort ):
  def construct( self, Type=None, method=None ):
    self.Type = Type
    self.method = method
    self._dsl.in_non_blocking_ifc = False

  def is_callee_port( s ):
    return True

  def is_caller_port( s ):
    return False

class NonBlockingInterface( Interface ):
  def construct( s, *args, **kwargs ):
    raise NotImplementedError("You can only instantiate NonBlockingCaller/NonBlockingCalleeIfc.")

  def __call__( s, *args, **kwargs ):
    return s.method( *args, **kwargs )

  def __str__( s ):
    return s._str_hook()

  def _str_hook( s ):
    return "{}".format( s._dsl.my_name )

class NonBlockingCalleeIfc( NonBlockingInterface ):
  def construct( s, Type=None, method=None, rdy=None ):
    s.Type = Type
    s.method = CalleePort( Type, method )
    s.rdy    = CalleePort( None, rdy )

    s.method._dsl.in_non_blocking_ifc = True
    s.rdy._dsl.in_non_blocking_ifc    = True

    s.method._dsl.is_rdy = False
    s.rdy._dsl.is_rdy    = True

class NonBlockingCallerIfc( NonBlockingInterface ):

  def construct( s, Type=None ):
    s.Type = Type

    s.method = CallerPort( Type )
    s.rdy    = CallerPort()

    s.method._dsl.in_non_blocking_ifc = True
    s.rdy._dsl.in_non_blocking_ifc    = True

    s.method._dsl.is_rdy = False
    s.rdy._dsl.is_rdy    = True
