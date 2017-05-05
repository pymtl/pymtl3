#=========================================================================
# UpdatesCall.py
#=========================================================================
# We override __call__ to facilitate connections.

from UpdatesExpl import verbose
from UpdatesImpl import UpdatesImpl

class UpdatesCall( UpdatesImpl ):

  def __call__( s, *args, **kwargs ):
    assert args == ()

    for (kw, item) in kwargs.iteritems():
      assert hasattr( s, kw ), "%s is not a member of class %s" % (kw, s.__class__)
      obj = getattr( s, kw )

      if isinstance( obj, list ):
        assert isinstance( item, dict ), "We only support a dictionary when '%s' is an array." % kw
        for idx in item:
          obj[idx] |= item[idx]

      else:
        obj |= item
    
    return s
