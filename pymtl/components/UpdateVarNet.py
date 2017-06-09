#=========================================================================
# UpdateVarNet.py
#=========================================================================

from UpdateVar   import UpdateVar
from Connectable import Connectable, Const
from errors      import InvalidConnectionError
from collections import defaultdict

import inspect # for error message

class UpdateVarNet( UpdateVar ):

  def connect( s, o1, o2 ):
    try:
      if isinstance( o1, int ) or isinstance( o2, int ): # special case
        if isinstance( o1, int ):
          o1, o2 = o2, o1 # o1 is signal, o2 is int
          assert isinstance( o1, Connectable )

        const = Const( o1.Type, o2 )
        const._parent = s
        o1._connect( const )

      else: # normal
        assert isinstance( o1, Connectable ) and isinstance( o2, Connectable )
        assert o1.Type == o2.Type
        o1._connect( o2 )
    except AssertionError as e:
      raise InvalidConnectionError( "\n{}".format(e) )

  def connect_pairs( s, *args ):
    if len(args) & 1 != 0:
       raise InvalidConnectionError( "Odd number ({}) of objects provided.".format( len(args) ) )

    for i in xrange(len(args)>>1):
      try:
        s.connect( args[ i<<1 ], args[ (i<<1)+1 ] )
      except InvalidConnectionError as e:
        raise InvalidConnectionError( "\n- In connect_pair, when connecting {}-th argument to {}-th argument\n{}\n " \
              .format( (i<<1)+1, (i<<1)+2 , e ) )

  def __call__( s, *args, **kwargs ):
    assert args == ()

    # The first loop checks if there is any invalid connection

    for (kw, item) in kwargs.iteritems():
      if not hasattr( s, kw ):
        raise InvalidConnectionError( "{} is not a member of class {}".format(kw, s.__class__) )

      item_valid = True

      obj = getattr( s, kw )

      if   isinstance( obj, list ): # out = {0:x, 1:y}
        if not isinstance( item, dict ):
          raise InvalidConnectionError( "We only support a dictionary when '{}' is an array.".format( kw ) )
        for idx in item:
          if isinstance( item[idx], int ):
            item_valid, error_idx = False, item[idx]
            break
      elif isinstance( item, tuple ):
        for x in item:
          if isinstance( item, int ):
            item_valid, error_idx = False, x
            break
      elif isinstance( item, int ):
        item_valid, error_idx = False, item

      if not item_valid:
        raise InvalidConnectionError( "Connecting port {} to constant {} can only be done through \"s.connect\".".format( kw, error_idx ) )

    # Then do the connection

    try:
      for (kw, item) in kwargs.iteritems():
        obj = getattr( s, kw )

        if   isinstance( obj, list ):
          for idx in item:
            obj[idx]._connect( item[idx] )
        elif isinstance( item, tuple ):
          for x in item:
            obj._connect( x )
        else:
          obj._connect( item )
    except AssertionError as e:
      raise InvalidConnectionError( "Invalid connection for {}:\n{}".format( kw, e ) )

    return s
