#-------------------------------------------------------------------------
# Utility linetracing function
#-------------------------------------------------------------------------

def valrdy_to_str( msg, val, rdy ):

  str_   = "{}".format( msg )
  nchars = max( len( str_ ), 15 )

  if       val and not rdy:
    str_ = "#".ljust( nchars )
  elif not val and     rdy:
    str_ = " ".ljust( nchars )
  elif not val and not rdy:
    str_ = ".".ljust( nchars )

  return str_.ljust( nchars )
