def freeze( obj ):
  if isinstance( obj, list ):
    return tuple( freeze( o ) for o in obj )
  return obj
