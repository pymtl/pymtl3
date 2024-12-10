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
    s.reqstream  = OStreamIfc( Type=ReqType )
    s.respstream = IStreamIfc( Type=RespType )

  def __str__( s ):
    return f"{s.reqstream}|{s.respstream}"

class ResponderIfc( Interface ):

  def construct( s, ReqType, RespType ):
    s.ReqType  = ReqType
    s.RespType = RespType
    s.reqstream  = IStreamIfc( Type=ReqType )
    s.respstream = OStreamIfc( Type=RespType )

  def __str__( s ):
    return f"{s.reqstream}|{s.respstream}"
