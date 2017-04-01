from pymtl import *
import math

class MemReqMsg( object ):

  TYPE_READ       = 0
  TYPE_WRITE      = 1
  # write no-refill
  TYPE_WRITE_INIT = 2
  TYPE_AMO_ADD    = 3
  TYPE_AMO_AND    = 4
  TYPE_AMO_OR     = 5
  TYPE_AMO_XCHG   = 6
  TYPE_AMO_MIN    = 7

  def __init__( s, opaque_nbits, addr_nbits, data_nbits ):
    s.type_  = mk_bits( 3 )
    s.opaque = mk_bits( opaque_nbits )
    s.addr   = mk_bits( addr_nbits   )
    s.len    = mk_bits( int( math.ceil( math.log( data_nbits>>3, 2) ) ) )
    s.data   = mk_bits( data_nbits   )

  def __call__( s ):
    return MemReqMsg( s.opaque.nbits, s.addr.nbits, s.data.nbits )

  def mk_rd( s, opaque, addr, len_ ):
    msg        = s()
    msg.type_  = msg.type_ ( MemReqMsg.TYPE_READ )
    msg.opaque = msg.opaque( opaque )
    msg.addr   = msg.addr  ( addr )
    msg.len    = msg.len   ( len_ )
    msg.data   = msg.data  ( 0 )
    return msg

  def mk_wr( s, opaque, addr, len_, data ):
    msg        = s()
    msg.type_  = msg.type_ ( MemReqMsg.TYPE_WRITE )
    msg.opaque = msg.opaque( opaque )
    msg.addr   = msg.addr  ( addr )
    msg.len    = msg.len   ( len_ )
    msg.data   = msg.data  ( data )
    return msg

  def mk_msg( s, type_, opaque, addr, len_, data ):
    msg        = s()
    msg.type_  = msg.type_ ( type_ )
    msg.opaque = msg.opaque( opaque )
    msg.addr   = msg.addr  ( addr )
    msg.len    = msg.len   ( len_ )
    msg.data   = msg.data  ( data )
    return msg

  def __str__( s ):
    if s.type_ == MemReqMsg.TYPE_READ:
      return "rd:{}:{}:{}".format( s.opaque, s.addr, ' '*(s.data.nbits>>2) )
    elif s.type_ == MemReqMsg.TYPE_WRITE:
      return "wr:{}:{}:{}".format( s.opaque, s.addr, s.data )
    elif s.type_ == MemReqMsg.TYPE_WRITE_INIT:
      return "in:{}:{}:{}".format( s.opaque, s.addr, s.data )
    elif s.type_ == MemReqMsg.TYPE_AMO_ADD:
      return "ad:{}:{}:{}".format( s.opaque, s.addr, s.data )
    elif s.type_ == MemReqMsg.TYPE_AMO_AND:
      return "an:{}:{}:{}".format( s.opaque, s.addr, s.data )
    elif s.type_ == MemReqMsg.TYPE_AMO_OR:
      return "or:{}:{}:{}".format( s.opaque, s.addr, s.data )
    elif s.type_ == MemReqMsg.TYPE_AMO_XCHG:
      return "xg:{}:{}:{}".format( s.opaque, s.addr, s.data )
    elif s.type_ == MemReqMsg.TYPE_AMO_MIN:
      return "mn:{}:{}:{}".format( s.opaque, s.addr, s.data )
    else:
      return "??:{}:{}:{}".format( s.opaque, s.addr, ' '*(s.data.nbits>>2) )

class MemRespMsg( object ):

  TYPE_READ       = 0
  TYPE_WRITE      = 1
  # write no-refill
  TYPE_WRITE_INIT = 2
  TYPE_AMO_ADD    = 3
  TYPE_AMO_AND    = 4
  TYPE_AMO_OR     = 5
  TYPE_AMO_XCHG   = 6
  TYPE_AMO_MIN    = 7

  def __init__( s, opaque_nbits, data_nbits ):
    s.type_  = mk_bits( 3 )
    s.opaque = mk_bits( opaque_nbits )
    s.test   = mk_bits( 2 )
    s.len    = mk_bits( int( math.ceil( math.log( data_nbits>>3, 2) ) ) )
    s.data   = mk_bits( data_nbits   )

  def __call__( s ):
    return MemRespMsg( s.opaque.nbits, s.data.nbits )

  def mk_rd( s, opaque, len_, data ):
    msg        = s()
    msg.type_  = msg.type_ ( MemReqMsg.TYPE_READ )
    msg.opaque = msg.opaque( opaque )
    msg.test   = msg.test  ( 0 )
    msg.len    = msg.len   ( len_ )
    msg.data   = msg.data  ( data )
    return msg

  def mk_wr( s, opaque, len_ ):
    msg        = s()
    msg.type_  = msg.type_ ( MemReqMsg.TYPE_WRITE )
    msg.opaque = msg.opaque( opaque )
    msg.test   = msg.test  ( 0 )
    msg.len    = msg.len   ( len_ )
    msg.data   = msg.data  ( 0 )
    return msg

  def mk_msg( s, type_, opaque, test, len_, data ):
    msg        = s()
    msg.type_  = msg.type_ ( type_ )
    msg.opaque = msg.opaque( opaque )
    msg.test   = msg.test  ( test )
    msg.len    = msg.len   ( len_ )
    msg.data   = msg.data  ( data )
    return msg

  def __str__( s ):
    if s.type_ == MemRespMsg.TYPE_READ:
      return "rd:{}:{}:{}".format( s.opaque, s.test, s.data )
    elif s.type_ == MemRespMsg.TYPE_WRITE:
      return "wr:{}:{}:{}".format( s.opaque, s.test, ' '*(s.data.nbits>>2) )
    elif s.type_ == MemRespMsg.TYPE_WRITE_INIT:
      return "in:{}:{}:{}".format( s.opaque, s.test, ' '*(s.data.nbits>>2) )
    elif s.type_ == MemRespMsg.TYPE_AMO_ADD:
      return "ad:{}:{}:{}".format( s.opaque, s.test, s.data )
    elif s.type_ == MemRespMsg.TYPE_AMO_AND:
      return "an:{}:{}:{}".format( s.opaque, s.test, s.data )
    elif s.type_ == MemRespMsg.TYPE_AMO_OR:
      return "or:{}:{}:{}".format( s.opaque, s.test, s.data )
    elif s.type_ == MemRespMsg.TYPE_AMO_XCHG:
      return "xg:{}:{}:{}".format( s.opaque, s.test, s.data )
    elif s.type_ == MemRespMsg.TYPE_AMO_MIN:
      return "mn:{}:{}:{}".format( s.opaque, s.test, s.data )
    else:
      return "??:{}:{}:{}".format( s.opaque, s.test, ' '*(s.data.nbits>>2) )
