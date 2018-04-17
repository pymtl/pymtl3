from NamedObject import NamedObject
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

  #-----------------------------------------------------------------------
  # Public APIs (only can be called after elaboration)
  #-----------------------------------------------------------------------

  def get_host_component( s ):
    try:
      return s._host
    except AttributeError:
      try:
        host = s
        while not host.is_component():
          host = host._parent_obj # go to the component
        s._host = host
        return s._host
      except AttributeError:
        raise NotElaboratedError()

  def get_parent_object( s ):
    try:
      return s._parent_obj
    except AttributeError:
      raise NotElaboratedError()

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
  def __init__( s, Type, v ):
    s.Type = Type
    s.const = v

  def __repr__( s ):
    return "{}({})".format( str(s.Type.__name__), s.const )

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
    s.Type = Type
    s._type_instance = None

    try:  Type.nbits
    except AttributeError: # not Bits type
      s._type_instance = Type()

    s._slice  = None # None -- not a slice of some wire by default
    s._attrs  = {}
    s._slices = {}
    s._top_level_signal = None

  def inverse( s ):
    pass

  def __getattr__( s, name ):
    if name.startswith("_"): # private variable
      return super( Signal, s ).__getattribute__( name )

    if name not in s.__dict__:
      _obj = getattr( s._type_instance, name )

      # if the object is Bits, we need to generate a Bits type
      try:
        x = s.__class__( mk_bits( _obj.nbits ) )
      except AttributeError:
        x = s.__class__( _obj.__class__ )

      x._type_instance = _obj

      x._parent_obj = s
      x._top_level_signal = s._top_level_signal

      x._full_name = s._full_name + "." + name
      x._my_name   = name

      s.__dict__[ name ] = s._attrs[ name ] = x

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
      x._parent_obj = s
      x._top_level_signal = s

      sl_str = "[{}:{}]".format( sl.start, sl.stop )

      x._my_name   = s._my_name + sl_str
      x._full_name = s._full_name + sl_str

      x._slice       = sl
      s.__dict__[ sl_tuple ] = s._slices[ sl_tuple ] = x

    return s.__dict__[ sl_tuple ]

  def default_value( s ):
    return s.Type()

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

  def get_top_level_signal( s ):
    return s if s._top_level_signal is None else s._top_level_signal

  def get_sibling_slices( s ):
    if s._slice:
      ret = s._parent_obj._slices.values()
      ret.remove( s )
      return ret
    return []

  def slice_overlap( s, other ):
    assert other._parent_obj is s._parent_obj, "You are only allowed to \
                                                pass in a sibling signal."
    return _overlap( s._slice, other._slice )

# These three subtypes are for type checking purpose
class Wire( Signal ):
  def inverse( s ):
    return Wire( s.Type )


class InVPort( Signal ):
  def inverse( s ):
    return OutVPort( s.Type )
  def is_input_value_port( s ):
    return True

class OutVPort( Signal ):
  def inverse( s ):
    return InVPort( s.Type )
  def is_output_value_port( s ):
    return True

class Interface( NamedObject, Connectable ):

  @property
  def Type( s ):
    return s._args

  def inverse( s ):
    s._inversed = True
    return s

  # Override
  # The same reason as __call__ connection. For s.x = A().inverse(),
  # inverse is executed before setattr, so we need to delay it ...

  def _construct( s ):
    if not s._constructed:
      if not s._kwargs: s.construct( *s._args )
      else:             s.construct( *s._args, **s._kwargs )

      if hasattr( s, "_inversed" ):
        for name, obj in s.__dict__.iteritems():
          if not name.startswith("_"):
            if isinstance( obj, Signal ):
              setattr( s, name, obj.inverse() )
            else:
              setattr( s, name, obj )

      s._constructed = True

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
