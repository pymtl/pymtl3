import inspect

class MetaPass(type):
  def __call__( cls, *args, **kwargs ):
    assert len(args) == 1 and not kwargs, "Only one parameter is accepted"

    obj = cls.__new__( cls )
    assert len( inspect.getargspec(obj.execute).args ) == 2, \
      "Please strictly pass in one parameter in \"execute\" method implementation"
    return cls.__new__( cls ).execute( args[0] )

class BasePass(object):
  __metaclass__ = MetaPass
