from pymtl.components import NamedObject
from pymtl.datatypes.Bits import mk_bits

class Connectable(object):

  def __new__( cls, *args, **kwargs ):
    inst = object.__new__( cls )

    inst._root      = inst # Use disjoint set to resolve connections
    inst._connected = [ inst ]

    return inst

  def _find_root( s ): # Disjoint set path compression
    if s._root == s:  return s
    s._root = s._root._find_root()
    return s._root

  def _connect( s, other ):
    assert isinstance( other, Connectable ), "Unconnectable object!"

    x = s._find_root()
    y = other._find_root()
    assert x != y, "Two nets are already unionized!"
    # assert x == s, "One net signal cannot have two drivers. \n%s" % \
                   # "Please check if the left side signal is already at left side in another connection."

    x._root = y # Merge myself to the other
    y._connected.extend( x._connected )
    x._connected = []

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
  assert False, "What the hell?"

class Wire( Connectable, NamedObject ):

  def __init__( s, Type ):
    s.Type    = Type
    s._nested = None # None means it's the top level Wire(Type)
    s._slice  = None # None means it's not a slice of some wire
    s._attrs  = {}
    s._slices = {}

  def __getattr__( s, name ):
    if name.startswith("_"): # private variable
      return s.__dict__[ name ]

    if name not in s.__dict__:
      x = Wire( getattr(s.Type, name) )
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
      x = Wire( mk_bits( sl.stop - sl.start) )
      x._nested = s
      x._slice  = sl
      s.__dict__[ sl_tuple ] = s._slices[ sl_tuple ] = x

    return s.__dict__[ sl_tuple ]

  def default_value( s ):
    return s.Type()

class InVPort( Wire ): pass
class OutVPort( Wire ): pass

class PortBundle( Connectable, NamedObject ):

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

    assert isinstance( other, WireBundle ),  "Invalid connection, %s <> %s." % (type(s).__name__, type(other).__name__)

    if not (type(s) is type(other)):
      assert  s.Type == other.Type, "Invalid connection, %s <> %s." % (type(s).__name__, type(other).__name__)
      print "warning: need to generate adapters for this connection between %s and %s." % (type(s).__name__, type(other).__name__)

    for name, obj in s.__dict__.iteritems():
      if not name.startswith("_"):
        recursive_connect( obj, getattr(other, name) )
