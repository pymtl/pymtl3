#=========================================================================
# UpdateVarNet.py
#=========================================================================

from UpdateVar   import UpdateVar
from Connectable import Connectable
from collections import defaultdict

class UpdateVarNet( UpdateVar ):

  def connect( s, o1, o2 ):
    assert isinstance( o1, Connectable ) and isinstance( o2, Connectable )
    assert o1.Type == o2.Type
    o1._connect( o2 )

  def connect_pairs( s, *args ):
    assert len(args) & 1 == 0, "Odd number of objects provided."
    for i in xrange(len(args)>>1):
      s.connect( args[ i<<1 ], args[ (i<<1)+1 ] )

  def __call__( s, *args, **kwargs ):
    assert args == ()

    for (kw, item) in kwargs.iteritems():
      assert hasattr( s, kw ), "%s is not a member of class %s" % (kw, s.__class__)
      obj = getattr( s, kw )

      if   isinstance( obj, list ):
        assert isinstance( item, dict ), "We only support a dictionary when '%s' is an array." % kw
        for idx in item:
          obj[idx]._connect( item[idx] )

      elif isinstance( item, tuple ):
        for x in item:
          obj._connect( x )
      else:
        obj._connect( item )

    return s
