"""
========================================================================
Send/RecvIfc adapters
========================================================================
CL/RTL adapters for send/recv interface.

Author : Yanghui Ou
  Date : Mar 07, 2019
"""
from __future__ import absolute_import, division, print_function

from pclib.ifcs.GuardedIfc import GuardedCallerIfc, guarded_ifc
from pclib.ifcs.SendRecvIfc import RecvIfcRTL, SendIfcRTL
from pymtl import *

from .ifcs_utils import enrdy_to_str
