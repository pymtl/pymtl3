#=========================================================================
# test_stateful_qeueues_test
#=========================================================================
# Tests for test_stateful using single entry queue
#
# Author: Yixiao Zhang
#   Date: June 10, 2019


import pytest

from pymtl3 import *
from pymtl3.datatypes import strategies as pst
from pymtl3.stdlib.cl import BypassQueueCL, PipeQueueCL, NormalQueueCL
from pymtl3.stdlib.rtl import BypassQueueRTL, PipeQueueRTL, NormalQueueRTL

from pymtl3.stdlib.test.pyh2.pyh2s import run_pyh2s
from pymtl3.stdlib.test.pyh2.RTL2CLWrapper import RTL2CLWrapper


def test_pyh2_directed():
  run_pyh2s( dut=NormalQueueRTL( Bits16, num_entries=2 ),
             ref=NormalQueueCL( num_entries=2 ) )

#-------------------------------------------------------------------------
# test_stateful_simple
#-------------------------------------------------------------------------

@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, BypassQueueRTL ),
                           ( PipeQueueCL, PipeQueueRTL ) ] )
def test_stateful_simple( QueueCL, QueueRTL ):
  run_pyh2s( QueueRTL( Bits16, 1 ), QueueCL( 1 ) )


#-------------------------------------------------------------------------
# test_stateful_bits_struct
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, BypassQueueRTL ),
                           ( PipeQueueCL, PipeQueueRTL ) ] )
def test_stateful_bits_struct( QueueCL, QueueRTL ):
  MsgType = mk_bitstruct( "MsgType", {
    'msg0' : Bits8,
    'msg1' : Bits8,
  })
  run_pyh2s( QueueRTL( MsgType, 1 ), QueueCL( 1 ) )

#-------------------------------------------------------------------------
# test_stateful_nested_bitstruct
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, BypassQueueRTL ),
                           ( PipeQueueCL, PipeQueueRTL ) ] )
def test_stateful_nested_struct( QueueCL, QueueRTL ):
  Msg1Type = mk_bitstruct( "Msg1Type", {
    'msg0': Bits8,
    'msg1': Bits8,
  })
  Msg2Type = mk_bitstruct( "MsgType", {
    'msg0': Bits8,
    'msg1': Msg1Type,
  })

  run_pyh2s( QueueRTL( Msg2Type, 1 ), QueueCL( 1 ) )

#-------------------------------------------------------------------------
# test_stateful_overwrite_simple
#-------------------------------------------------------------------------
def test_stateful_overwrite_simple():
  run_pyh2s( BypassQueueRTL( Bits32, 1 ), BypassQueueCL( 1 ),
             custom_strategy={ 'enq.msg': range(0, 12) } )

def test_stateful_overwrite_wrong_strat():
  try:
    run_pyh2s( BypassQueueRTL( Bits32, 1 ), BypassQueueCL( 1 ),
               custom_strategy={ 'enq.msg': (0, 12) } )
  except TypeError as e:
    print(e)
    return
  raise Exception("Should've thrown TypeError")

def test_stateful_overwrite_wrong_name():
  try:
    run_pyh2s( BypassQueueRTL( Bits32, 1 ), BypassQueueCL( 1 ),
               custom_strategy={ 'enq.ms': range(0, 12) } )
  except ValueError as e:
    print(e)
    return
  raise Exception("Should've thrown ValueError")

def test_stateful_overwrite_wrong_field():
  try:
    run_pyh2s( BypassQueueRTL( Bits32, 1 ), BypassQueueCL( 1 ),
               custom_strategy={ 'enq.msg.sb': range(0, 12) } )
  except TypeError as e:
    print(e)
    return
  raise Exception("Should've thrown TypeError")

#-------------------------------------------------------------------------
# test_stateful_overwrite_nested
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, BypassQueueRTL ),
                           ( PipeQueueCL, PipeQueueRTL ) ] )
def test_stateful_overwrite_nested_correct( QueueCL, QueueRTL ):
  Msg1Type = mk_bitstruct( "Msg1Type", {
    'msg0': Bits32,
    'msg1': Bits8,
  })
  MsgType = mk_bitstruct( "MsgType", {
    'msg0': Bits8,
    'msg1': Msg1Type,
  })

  run_pyh2s( QueueRTL( MsgType, 1 ), QueueCL( 1 ),
      custom_strategy={'enq.msg.msg0': pst.bits( 8, min_value=0, max_value=5 ),
                       'enq.msg.msg1.msg1': pst.bits( 8, min_value=0xf0, max_value=0xff )
      })

  # specify composite strategy directly
  run_pyh2s( QueueRTL( MsgType, 1 ), QueueCL( 1 ),
      custom_strategy={'enq.msg.msg1': pst.bitstructs( Msg1Type )} )

# Strategy for a field and its subfield are not allowed
def test_stateful_overwrite_nested_multi_writer():
  Msg1Type = mk_bitstruct( "Msg1Type", {
    'msg0': Bits32,
    'msg1': Bits8,
  })
  MsgType = mk_bitstruct( "MsgType", {
    'msg0': Bits8,
    'msg1': Msg1Type,
  })

  try:
    run_pyh2s( BypassQueueRTL( MsgType, 1 ), BypassQueueCL( 1 ),
        custom_strategy={
          'enq.msg.msg1.msg1': pst.bits( 8, min_value=100, max_value=200 ),
          'enq.msg.msg1': pst.bitstructs( MsgType ),
        })
    raise Exception("Should've thrown TypeError")
  except TypeError as e:
    print(e)

  try:
    run_pyh2s( BypassQueueRTL( MsgType, 1 ), BypassQueueCL( 1 ),
        custom_strategy={
          'enq.msg.msg1': pst.bitstructs( MsgType ),
          'enq.msg.msg1.msg1': pst.bits( 8, min_value=100, max_value=200 ),
        })
    raise Exception("Should've thrown TypeError")
  except TypeError as e:
    print(e)

  try:
    run_pyh2s( BypassQueueRTL( MsgType, 1 ), BypassQueueCL( 1 ),
        custom_strategy={
          'enq.msg.msg1.msg1': pst.bits( 8, min_value=100, max_value=200 ),
          'enq.msg': pst.bitstructs( MsgType ),
        })
    raise Exception("Should've thrown TypeError")
  except TypeError as e:
    print(e)

  try:
    run_pyh2s( BypassQueueRTL( MsgType, 1 ), BypassQueueCL( 1 ),
        custom_strategy={
          'enq.msg': pst.bitstructs( MsgType ),
          'enq.msg.msg1.msg1': pst.bits( 8, min_value=100, max_value=200 ),
        })
    raise Exception("Should've thrown AssertionError")
  except TypeError as e:
    print(e)

# must be strategy
def test_stateful_overwrite_nested_wrong_type():
  Msg1Type = mk_bitstruct( "Msg1Type", {
    'msg0': Bits8,
    'msg1': Bits8,
  })
  MsgType = mk_bitstruct( "MsgType", {
    'msg0': Bits8,
    'msg1': Msg1Type,
  })
  try:
    run_pyh2s( BypassQueueRTL( MsgType, 1 ), BypassQueueCL( 1 ), custom_strategy={ 'enq.msg.msg1': 1 } )
  except TypeError as e:
    print( e )
    return
  raise Exception("Should've thrown AssertionError")
