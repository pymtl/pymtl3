"""
==========================================================================
 master_minion_ifc.py
==========================================================================
Master/minion send/recv interface implementations at CL and RTL.

 Author: Shunning Jiang
   Date: Jan 28, 2020
"""
from pymtl3 import *

from .SendRecvIfc import RecvIfcRTL, SendIfcRTL

#-------------------------------------------------------------------------
# CL interfaces
#-------------------------------------------------------------------------

# There is no custom connect method in CL ifcs.
# For MasterCL-MinionRTL and MasterRTL-MinionCL connections, we just need
# to connect by name and leverage the custom connect method of the nested
# Send/RecvIfc.

class MasterIfcCL( Interface ):
  def construct( s, Types, resp=None, resp_rdy=None ):
    s.Types = Types
    s.req  = CallerIfcCL( Type=Types.req )
    s.resp = CalleeIfcCL( Type=Types.resp, method=resp, rdy=resp_rdy )
  def __str__( s ):
    return f"{s.req}|{s.resp}"

class MinionIfcCL( Interface ):
  def construct( s, Types, req=None, req_rdy=None ):
    s.Types = Types
    s.req  = CalleeIfcCL( Type=Types.req, method=req, rdy=req_rdy )
    s.resp = CallerIfcCL( Type=Types.resp )
  def __str__( s ):
    return f"{s.req}|{s.resp}"

#-------------------------------------------------------------------------
# RTL interfaces
#-------------------------------------------------------------------------
# There is no custom connect method in CL ifcs.
# For MasterCL-MinionRTL and MasterRTL-MinionCL connections, we just need
# to connect by name and leverage the custom connect method of the nested
# Send/RecvIfc.

class MasterIfcRTL( Interface ):
  def construct( s, Types ):
    s.Types = Types
    s.req  = SendIfcRTL( Type=Types.req )
    s.resp = RecvIfcRTL( Type=Types.resp )
  def __str__( s ):
    return f"{s.req}|{s.resp}"

class MinionIfcRTL( Interface ):
  def construct( s, Types ):
    s.Types = Types
    s.req  = RecvIfcRTL( Type=Types.req )
    s.resp = SendIfcRTL( Type=Types.resp )
  def __str__( s ):
    return f"{s.req}|{s.resp}"
