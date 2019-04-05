#=========================================================================
# ifcs_utils.py
#=========================================================================
# Utility functions for ifcs.
#
# Author: Yanghui Ou
#   Date: Feb 21, 2019

from pymtl import *

#-------------------------------------------------------------------------
# enrdy_to_str
#-------------------------------------------------------------------------
# A heler function that convert en/rdy interface into string.

def enrdy_to_str( msg, en, rdy, trace_len=15 ):

  _str   = "{}".format( msg )

  if en and not rdy:
    _str = "X".ljust( trace_len ) # Not allowed
  elif not en and rdy:
    _str = " ".ljust( trace_len ) # Idle
  elif not en and not rdy:
    _str = "#".ljust( trace_len ) # Stall

  return _str.ljust( trace_len )
