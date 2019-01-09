from pymtl import *

import py

mem_msg_cache = dict()
def mk_mem_msg( o, a, d ):
  if (o,a,d) in mem_msg_cache:
    return mem_msg_cache[ (o,a,d) ]
  exec py.code.Source( template.format( o, a, d ) ).compile() in globals()
  return eval( "MemReqMsg_{0}_{1}_{2}, MemRespMsg_{0}_{2}".format( o, a, d ) )

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

  def __init__( s, type_=TYPE_READ, opaque=0, addr=0, len_=0, data=0 ):
    s.type_  = Bits4( type_ )
    s.opaque = Bits{0}( opaque )
    s.addr   = Bits{1}( addr )
    s.len_   = Bits2( len_ )
    s.data   = Bits{2}( data )

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

  opaque_nbits = {0}
  data_nbits   = {2}

  def __init__( s, type_=0, opaque=0, test=0, len_=0, data=0 ):
    s.type_  = Bits4( type_ )
    s.opaque = Bits{0}( opaque )
    s.test   = Bits2( test )
    s.len_   = Bits2( len_ )
    s.data   = Bits{2}( data )

mem_msg_cache[ ({0},{1},{2}) ] = MemReqMsg_{0}_{1}_{2}, MemRespMsg_{0}_{2}
"""
