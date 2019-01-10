from pymtl import *

import py

mem_msg_cache = dict()
def mk_mem_msg( o, a, d ):
  if (o,a,d) in mem_msg_cache:
    return mem_msg_cache[ (o,a,d) ]
  exec py.code.Source( template.format( o, a, d ) ).compile() in globals()
  return eval( "MemReqMsg_{0}_{1}_{2}, MemRespMsg_{0}_{2}".format( o, a, d ) )

def msg_to_str( msg, width ):
  return ("" if msg is None else str(msg)).ljust(width)

template = """
class MemReqMsg_{0}_{1}_{2}( object ):
  TYPE_READ       = 0
  TYPE_WRITE      = 1
  # write no-refill
  TYPE_WRITE_INIT = 2
  TYPE_AMO_ADD    = 3
  TYPE_AMO_AND    = 4
  TYPE_AMO_OR     = 5
  TYPE_AMO_SWAP   = 6
  TYPE_AMO_MIN    = 7
  TYPE_AMO_MINU   = 8
  TYPE_AMO_MAX    = 9
  TYPE_AMO_MAXU   = 10
  TYPE_AMO_XOR    = 11

  opaque_nbits = {0}
  addr_nbits   = {1}
  data_nbits   = {2}

  type_str_mapping = {{
    TYPE_READ       : "rd",
    TYPE_WRITE      : "wr",
    TYPE_WRITE_INIT : "in",
    TYPE_AMO_ADD    : "ad",
    TYPE_AMO_AND    : "an",
    TYPE_AMO_OR     : "or",
    TYPE_AMO_SWAP   : "sw",
    TYPE_AMO_MIN    : "mi",
    TYPE_AMO_MINU   : "mu",
    TYPE_AMO_MAX    : "mx",
    TYPE_AMO_MAXU   : "xu",
    TYPE_AMO_XOR    : "xo",
  }}

  def __init__( s, type_=TYPE_READ, opaque=0, addr=0, len_=0, data=0 ):
    s.type_  = Bits4( type_ )
    s.opaque = Bits{0}( opaque )
    s.addr   = Bits{1}( addr )
    s.len_   = Bits2( len_ )
    s.data   = Bits{2}( data )

  def __str__( s ):
    return "{{}}:{{}}:{{}}:{{}}".format(
      MemReqMsg_{0}_{1}_{2}.type_str_mapping[int(s.type_)],
      s.opaque, s.addr, s.data,
    )

  def __eq__( s, other ):
    return s.type_ == other.type_ and \
           s.opaque == other.opaque and \
           s.addr == other.addr and \
           s.len_ == other.len_ and \
           s.data == other.data

  def __ne__( s, other ):
    return s.type_ != other.type_ or \
           s.opaque != other.opaque or \
           s.addr != other.addr or \
           s.len_ != other.len_ or \
           s.data != other.data

class MemRespMsg_{0}_{2}( object ):
  TYPE_READ       = 0
  TYPE_WRITE      = 1
  # write no-refill
  TYPE_WRITE_INIT = 2
  TYPE_AMO_ADD    = 3
  TYPE_AMO_AND    = 4
  TYPE_AMO_OR     = 5
  TYPE_AMO_SWAP   = 6
  TYPE_AMO_MIN    = 7
  TYPE_AMO_MINU   = 8
  TYPE_AMO_MAX    = 9
  TYPE_AMO_MAXU   = 10
  TYPE_AMO_XOR    = 11

  type_str_mapping = {{
    TYPE_READ       : "rd",
    TYPE_WRITE      : "wr",
    TYPE_WRITE_INIT : "in",
    TYPE_AMO_ADD    : "ad",
    TYPE_AMO_AND    : "an",
    TYPE_AMO_OR     : "or",
    TYPE_AMO_SWAP   : "sw",
    TYPE_AMO_MIN    : "mi",
    TYPE_AMO_MINU   : "mu",
    TYPE_AMO_MAX    : "mx",
    TYPE_AMO_MAXU   : "xu",
    TYPE_AMO_XOR    : "xo",
  }}

  opaque_nbits = {0}
  data_nbits   = {2}

  def __init__( s, type_=0, opaque=0, test=0, len_=0, data=0 ):
    s.type_  = Bits4( type_ )
    s.opaque = Bits{0}( opaque )
    s.test   = Bits2( test )
    s.len_   = Bits2( len_ )
    s.data   = Bits{2}( data )

  def __str__( s ):
    return "{{}}:{{}}:{{}}:{{}}".format(
      MemRespMsg_{0}_{2}.type_str_mapping[int(s.type_)],
      s.opaque, s.test, s.data,
    )

  def __eq__( s, other ):
    return s.type_ == other.type_ and \
           s.opaque == other.opaque and \
           s.test == other.test and \
           s.len_ == other.len_ and \
           s.data == other.data

  def __ne__( s, other ):
    return s.type_ != other.type_ or \
           s.opaque != other.opaque or \
           s.test != other.test or \
           s.len_ != other.len_ or \
           s.data != other.data

mem_msg_cache[ ({0},{1},{2}) ] = MemReqMsg_{0}_{1}_{2}, MemRespMsg_{0}_{2}
"""
