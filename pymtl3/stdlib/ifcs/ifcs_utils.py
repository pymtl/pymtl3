"""
========================================================================
ifcs_utils.py
========================================================================
Utility functions for ifcs.

Author: Yanghui Ou
  Date: Feb 21, 2019
"""
#-------------------------------------------------------------------------
# enrdy_to_str
#-------------------------------------------------------------------------

def enrdy_to_str( msg, en, rdy, trace_len=15 ):

  _str   = "{}".format( msg )

  if en and not rdy:
    _str = "X".ljust( trace_len ) # Not allowed
  elif not en and rdy:
    _str = " ".ljust( trace_len ) # Idle
  elif not en and not rdy:
    _str = "#".ljust( trace_len ) # Stall

  return _str.ljust( trace_len )

#-------------------------------------------------------------------------
#  valrdy_to_str
#-------------------------------------------------------------------------

def valrdy_to_str( msg, val, rdy, trace_len=15 ):

  _str   = "{}".format( msg )

  if       val and not rdy:
    _str = "#".ljust( trace_len )
  elif not val and     rdy:
    _str = " ".ljust( trace_len )
  elif not val and not rdy:
    _str = ".".ljust( trace_len )

  return _str.ljust( trace_len )
