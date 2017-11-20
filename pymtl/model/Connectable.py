from NamedObject import NamedObject
from pymtl.datatypes import mk_bits

class Connectable(object):

  def __new__( cls, *args, **kwargs ):
    inst = super( Connectable, cls ).__new__( cls )

    inst._adjs = []
    return inst

  # As disjoint set is good for unionize nodes but not detaching subtrees,
  # I have to give up.

  def _connect( s, other ):
    assert isinstance( other, Connectable ), "Unconnectable object!"

    s._adjs.append( other )
    other._adjs.append( s ) # bidirectional

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
    s._nested = None # no member
    s._slice  = None # not slicable

  def __repr__( s ):
    return "{}({})".format( str(s.Type.__name__), s.const )

class Signal( Connectable, NamedObject ):

  def __init__( s, Type ):
    s.Type    = Type
    s._nested = None # None means it's the top level Wire(Type)
    s._slice  = None # None means it's not a slice of some wire
    s._attrs  = {}
    s._slices = {}

  def inverse( s ):
    pass

  def __getattr__( s, name ):
    if name.startswith("_"): # private variable
      return super( Signal, s ).__getattribute__( name )

    if name not in s.__dict__:
      x = s.__class__( getattr(s.Type, name) )
      x._nested          = s
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
      x._nested = s
      x._slice  = sl
      s.__dict__[ sl_tuple ] = s._slices[ sl_tuple ] = x

    return s.__dict__[ sl_tuple ]

  def _connect( s, other ):
    assert s.Type == other.Type, "Type mismatch {} != {}".format( s.Type, other.Type )
    super( Signal, s )._connect( other )

  def default_value( s ):
    return s.Type()

# These three subtypes are for type checking purpose
class Wire( Signal ):
  def inverse( s ):
    return Wire( s.Type )

class InVPort( Signal ):
  def inverse( s ):
    return OutVPort( s.Type )

class OutVPort( Signal ):
  def inverse( s ):
    return InVPort( s.Type )

class Interface( Connectable, NamedObject ):

  def inverse( s ):
    inv = s
    # Berkin: is it necessary to create a new object here? This creates
    # problems when the interface has parameters, and it would be clunky
    # to carry those parameters to the new object.
    #inv = s.__class__()
    for name, obj in inv.__dict__.iteritems():
      if isinstance( obj, Signal ):
        setattr( inv, name, obj.inverse() )
      else:
        setattr( inv, name, obj )
    return inv

  # Override
  def _connect( s, other ):
    # Expand the list when needed. Only connect connectables and return,
    # inheritance will figure out what to do with Wire/WireBundle

    def recursive_connect( s_obj, other_obj ):
      if isinstance( s_obj, Connectable ):
        s_obj._connect( other_obj )
      if   isinstance( s_obj, list ):
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
