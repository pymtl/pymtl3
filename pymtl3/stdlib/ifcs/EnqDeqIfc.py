"""
========================================================================
EnqDeqIfc.py
========================================================================
RTL implementation of deq and enq interface.

Author: Yanghui Ou
  Date: Mar 21, 2019
"""
from pymtl3 import *
from pymtl3.stdlib.connects import connect_pairs

from .GetGiveIfc import GiveIfcRTL
from .SendRecvIfc import RecvIfcRTL

#-------------------------------------------------------------------------
# EnqIfcRTL
#-------------------------------------------------------------------------

class EnqIfcRTL( RecvIfcRTL ):
  pass

#-------------------------------------------------------------------------
# DeqIfcRTL
#-------------------------------------------------------------------------

class DeqIfcRTL( GiveIfcRTL ):
  pass
