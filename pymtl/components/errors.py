
class SignalTypeError( Exception ):
  """ Raise when a declared signal is of wrong type """

class MultiWriterError( Exception ):
  """ Raise when a variable is written by multiple update blocks/nets """
  def __init__( self, nets ):
    return super( NoWriterError, self ).__init__( \
    "The following nets need drivers.\nNet:\n - {} ".format(
      "\nNet:\n - ".join( [ "\n - ".join( [ repr(x) for x in y ] )
                            for y in net ]) ) )

class NoWriterError( Exception ):
  """ Raise when a net has no writer (driver) """
  def __init__( self, nets ):
    return super( NoWriterError, self ).__init__( \
    "The following nets need drivers.\nNet:\n - {} ".format(
      "\nNet:\n - ".join( [ "\n - ".join( [ repr(x) for x in y ] )
                            for y in net ]) ) )

class VarNotDeclaredError( Exception ):
  """ Raise when a variable in an update block is not declared """
  def __init__( self, obj, field, blk=None, lineno=0 ):
    self.obj    = obj
    self.field  = field
    self.blk    = blk
    # TODO add inspect file path
    return super( VarNotDeclaredError, self ).__init__( \
      "Object {} of class {} does not have field <{}> ({}.{})\n - Occurred at Line {} of {}".format( \
      repr(obj), obj.__class__.__name__, field, repr(obj), lineno, blk.__name__ ) )

class InvalidVarError( Exception ):
  """ Raise when a variable in an update block is not declared or the
      declaration is not consistent with references """

class UpblkCyclicError( Exception ):
  """ Raise when update blocks have cyclic dependencies """
