def guard_rdy( cond ):
  def real_guard( method ):
    setattr( method, "guard", "rdy" )
    setattr( method, "rdy", cond )
    return method
  return real_guard
