"""
========================================================================
Requester and Responder interfaces
========================================================================
RTL Requester and Responder interfaces.

Author : Shunning Jiang, Peitian Pan
  Date : Aug 26, 2022
"""

from pymtl3 import *
from pymtl3.stdlib.stream.ifcs import IStreamIfc, OStreamIfc

class RequesterIfc( Interface ):

  def construct( s, ReqType, RespType ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.req = OStreamIfc( Type=ReqType )
    s.rsp = IStreamIfc( Type=RespType )

  def __str__( s ):
    return f"{s.req}|{s.rsp}"

class ResponderIfc( Interface ):

  def construct( s, ReqType, RespType ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.req = IStreamIfc( Type=ReqType )
    s.rsp = OStreamIfc( Type=RespType )

  def __str__( s ):
    return f"{s.req}|{s.rsp}"
