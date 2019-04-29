# =========================================================================
# MemMsg.py
# =========================================================================
# New memory message type implementation.
#
# Author : Shunning Jiang
# Date   : Mar 12, 2018

from builtins import str
from builtins import object
from pymtl import *

import py

_mem_req_msg_cache = dict()
_mem_resp_msg_cache = dict()


def mk_mem_msg(o, a, d):
    return mk_mem_req_msg(o, a, d), mk_mem_resp_msg(o, d)


def mk_mem_req_msg(o, a, d):
    if (o, a, d) in _mem_req_msg_cache:
        return _mem_req_msg_cache[(o, a, d)]
    exec(py.code.Source(_req_template.format(o, a, d)).compile(), globals())
    return _mem_req_msg_cache[(o, a, d)]


def mk_mem_resp_msg(o, d):
    if (o, d) in _mem_resp_msg_cache:
        return _mem_resp_msg_cache[(o, d)]
    exec(py.code.Source(_resp_template.format(o, d)).compile(), globals())
    return _mem_resp_msg_cache[(o, d)]


class MemMsgType(object):
    READ = 0
    WRITE = 1
    # write no-refill
    WRITE_INIT = 2
    AMO_ADD = 3
    AMO_AND = 4
    AMO_OR = 5
    AMO_SWAP = 6
    AMO_MIN = 7
    AMO_MINU = 8
    AMO_MAX = 9
    AMO_MAXU = 10
    AMO_XOR = 11

    str = {
        READ: "rd",
        WRITE: "wr",
        WRITE_INIT: "in",
        AMO_ADD: "ad",
        AMO_AND: "an",
        AMO_OR: "or",
        AMO_SWAP: "sw",
        AMO_MIN: "mi",
        AMO_MINU: "mu",
        AMO_MAX: "mx",
        AMO_MAXU: "xu",
        AMO_XOR: "xo",
    }


def msg_to_str(msg, width):
    return ("" if msg is None else str(msg)).ljust(width)


_req_template = """
class MemReqMsg_{0}_{1}_{2}( object ):
  opaque_nbits = {0}
  addr_nbits   = {1}
  data_nbits   = {2}

  def __init__( s, type_=MemMsgType.READ, opaque=0, addr=0, len_=0, data=0 ):
    s.type_  = Bits4( type_ )
    s.opaque = Bits{0}( opaque )
    s.addr   = Bits{1}( addr )
    s.len    = Bits2( len_ )
    s.data   = Bits{2}( data )

  def __str__( s ):
    return "{{}}:{{}}:{{}}:{{}}".format(
    MemMsgType.str[ int(s.type_) ],
      s.opaque, s.addr,
      (" "*(s.data_nbits/4)) if int(s.type_) == MemMsgType.READ else s.data,
    )

  def __eq__( s, other ):
    return s.type_ == other.type_ and \
           s.opaque == other.opaque and \
           s.addr == other.addr and \
           s.len == other.len and \
           s.data == other.data
  def __ne__( s, other ):
    return s.type_ != other.type_ or \
           s.opaque != other.opaque or \
           s.addr != other.addr or \
           s.len != other.len or \
           s.data != other.data

  @classmethod
  def mk_rd( cls, opaque, addr, len_ ):
    return cls( type_=MemMsgType.READ, opaque=opaque, addr=addr, len_=len_ )

  @classmethod
  def mk_wr( cls, opaque, addr, len_, data ):
    return cls( type_=MemMsgType.WRITE, opaque=opaque, addr=addr, len_=len_, data=data )
_mem_req_msg_cache[ ({0},{1},{2}) ] = MemReqMsg_{0}_{1}_{2}
"""
_resp_template = """
class MemRespMsg_{0}_{1}( object ):
  opaque_nbits = {0}
  data_nbits   = {1}

  def __init__( s, type_=MemMsgType.READ, opaque=0, test=0, len_=0, data=0 ):
    s.type_  = Bits4( type_ )
    s.opaque = Bits{0}( opaque )
    s.test   = Bits2( test )
    s.len    = Bits2( len_ )
    s.data   = Bits{1}( data )

  def __str__( s ):
    return "{{}}:{{}}:{{}}:{{}}".format(
      MemMsgType.str[int(s.type_)],
      s.opaque, s.test,
      (" "*(s.data_nbits/4)) if int(s.type_) == MemMsgType.WRITE else s.data
    )

  def __eq__( s, other ):
    return s.type_ == other.type_ and \
           s.opaque == other.opaque and \
           s.test == other.test and \
           s.len == other.len and \
           s.data == other.data

  def __ne__( s, other ):
    return s.type_ != other.type_ or \
           s.opaque != other.opaque or \
           s.test != other.test or \
           s.len != other.len or \
           s.data != other.data

  @classmethod
  def mk_rd( cls, opaque, len_, data ):
    return cls( MemMsgType.READ, opaque, 0, len_, data )

  @classmethod
  def mk_wr( cls, opaque, len_ ):
    return cls( MemMsgType.WRITE, opaque, 0, len_ )

_mem_resp_msg_cache[ ({0},{1}) ] = MemRespMsg_{0}_{1}
"""
