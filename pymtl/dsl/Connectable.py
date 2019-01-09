#=========================================================================
# Connectable.py
#=========================================================================
# Wires, ports, and interfaces, all inherited from Connectable.
#
# Author : Shunning Jiang
# Date   : Apr 16, 2018

from NamedObject import NamedObject, DSLMetadata
from pymtl.datatypes import mk_bits
from errors import InvalidConnectionError

class Connectable(object):

  # I've given up maintaining adjacency list or disjoint set locally since
  # we need to easily disconnect things

  def _connect( s, other, adjacency_dict ):
    assert isinstance( other, Connectable ), "Unconnectable object!"

    if other in adjacency_dict[s]:
      raise InvalidConnectionError( "This pair of signals are already connected."\
                                    "\n - {} \n - {}".format( s, other ) )

    adjacency_dict[s].add( other )
    adjacency_dict[other].add( s )

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
    return "{}({})".format( str(s._dsl.Type.__name__), s._dsl.const )

  def get_parent_object( s ):
    try:
      return s._dsl.parent_obj
    except AttributeError:
      raise NotElaboratedError()

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

  def get_sibling_slices( s ):
    return []

  def is_component( s ):
    return False

  def is_signal( s ):
    return False

  def is_interface( s ):
    return False

class Signal( NamedObject, Connectable ):

  def __init__( s, Type ):
    s._dsl.Type = Type
    s._dsl.type_instance = None

    try:  Type.nbits
    except AttributeError: # not Bits type
      s._dsl.type_instance = Type()

    s._dsl.slice  = None # None -- not a slice of some wire by default
    s._dsl.attrs  = {}
    s._dsl.slices = {}
    s._dsl.top_level_signal = None

  def inverse( s ):
    pass

  def __getattr__( s, name ):
    if name.startswith("_"): # private variable
      return super( Signal, s ).__getattribute__( name )

    if name not in s.__dict__:
      _obj = getattr( s._dsl.type_instance, name )

      # if the object is Bits, we need to generate a Bits type
      try:
        x = s.__class__( mk_bits( _obj.nbits ) )
      except AttributeError:
        x = s.__class__( _obj.__class__ )

      x._dsl.type_instance = _obj

      x._dsl.parent_obj = s
      x._dsl.top_level_signal = s._dsl.top_level_signal

      x._dsl.full_name = s._dsl.full_name + "." + name
      x._dsl.my_name   = name

      s.__dict__[ name ] = s._dsl.attrs[ name ] = x

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

  def get_top_level_signal( s ):
    top = s._dsl.top_level_signal
    return s if top is None else top

  def get_sibling_slices( s ):
    if s._dsl.slice:
      parent = s.get_parent_object()
      ret = parent._dsl.slices.values()
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

class InVPort( Signal ):
  def inverse( s ):
    return OutVPort( s._dsl.Type )
  def is_input_value_port( s ):
    return True

class OutVPort( Signal ):
  def inverse( s ):
    return InVPort( s._dsl.Type )
  def is_output_value_port( s ):
    return True

class Interface( NamedObject, Connectable ):

  @property
  def Type( s ):
    return s._dsl.args

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
      try:  inversed = s._dsl.inversed
      except AttributeError: pass

      if inversed:
        for name, obj in s.__dict__.iteritems():
          if not name.startswith("_"):
            if isinstance( obj, Signal ):
              setattr( s, name, obj.inverse() )
            else:
              setattr( s, name, obj )

      s._dsl.constructed = True

  def _connect( s, other, edges ):
    # Expand the list when needed. Only connect connectables and return,
    # inheritance will figure out what to do with Wire/WireBundle

    def recursive_connect( s_obj, other_obj ):
      if hasattr( s_obj, "_connect" ):
        s_obj._connect( other_obj, edges )

      elif isinstance( s_obj, list ):
        for i in xrange(len(s_obj)):
          recursive_connect( s_obj[i], other_obj[i] )

    assert isinstance( other, Interface ),  "Invalid connection, %s <> %s." % (type(s).__name__, type(other).__name__)

    # if not (type(s) is type(other)):
      # assert  s.Type == other.Type, "Invalid connection, %s <> %s." % (type(s).__name__, type(other).__name__)
      # print "warning: need to generate adapters for this connection between %s and %s." % (type(s).__name__, type(other).__name__)

    for name, obj in s.__dict__.iteritems():
      if not name.startswith("_"):
        assert hasattr( other, name )
        recursive_connect( obj, getattr( other, name ) )

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

  def __init__( self ):
    self.method = None

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

class CallerPort( MethodPort ):
  def __init__( self ):
    self.method = None

  def is_callee_port( s ):
    return False

  def is_caller_port( s ):
    return True


class CalleePort( MethodPort ):
  def __init__( self, method=None ):
    self.method = method

  def is_callee_port( s ):
    return True

  def is_caller_port( s ):
    return False
