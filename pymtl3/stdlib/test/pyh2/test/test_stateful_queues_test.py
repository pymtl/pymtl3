#=========================================================================
# test_stateful_qeueues_test
#=========================================================================
# Tests for test_stateful using single entry queue
#
# Author: Yixiao Zhang
#   Date: June 10, 2019

from collections import deque

import pytest

from pymtl3 import *

from .test_stateful import get_strategy_from_type, run_test_state_machine
from .test_wrapper import *

from pymtl3.stdlib.cl  import PipeQueueCL, BypassQueueCL
from pymtl3.stdlib.rtl import PipeQueueRTL, BypassQueueRTL

#-------------------------------------------------------------------------
# test_stateful_simple
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, BypassQueueRTL ),
                           ( PipeQueueCL, PipeQueueRTL ) ] )
def test_stateful_simple( QueueCL, QueueRTL ):
  run_test_state_machine( RTL2CLWrapper( QueueRTL( Bits16, 1 ) ), QueueCL( 1 ) )


#-------------------------------------------------------------------------
# test_stateful_bits_struct
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, BypassQueueRTL ),
                           ( PipeQueueCL, PipeQueueRTL ) ] )
def test_stateful_bits_struct( QueueCL, QueueRTL ):
  Msg1Type = mk_bitstruct( "Msg1Type", [( 'msg0', Bits8 ),
                                         ( 'msg1', Bits8 ) ] )
  run_test_state_machine(
      RTL2CLWrapper(
          QueueRTL(
              mk_bitstruct( "MsgType", [( 'msg0', Bits8 ),
                                         ( 'msg1', Msg1Type ) ] ) ) ),
      QueueCL( 1 ) )


#-------------------------------------------------------------------------
# test_stateful_overwrite_simple
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, BypassQueueRTL ),
                           ( PipeQueueCL, PipeQueueRTL ) ] )
def test_stateful_overwrite_simple( QueueCL, QueueRTL ):
  run_test_state_machine(
      RTL2CLWrapper( QueueRTL( Bits32 ) ),
      QueueCL( 1 ),
      argument_strategy=[( 'enq.msg', st.integers( min_value=0,
                                                   max_value=11 ) ) ] )
  # must be strategy
  try:
    run_test_state_machine(
        RTL2CLWrapper( QueueRTL( Bits32 ) ),
        QueueCL( 1 ),
        argument_strategy=[( 'enq.msg', 1 ) ] )
    assert False
  except TypeError as e:
    print( e )

  # unknown field
  try:
    run_test_state_machine(
        RTL2CLWrapper( QueueRTL( Bits32 ) ),
        QueueCL( 1 ),
        argument_strategy=[( 'enq.msg2', st.integers(
            min_value=0, max_value=11 ) ) ] )
    assert False
  except AssertionError as e:
    print( e )


#-------------------------------------------------------------------------
# test_stateful_overwrite_nested
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, BypassQueueRTL ),
                           ( PipeQueueCL, PipeQueueRTL ) ] )
def test_stateful_overwrite_nested( QueueCL, QueueRTL ):
  Msg1Type = mk_bit_struct( "Msg1Type", [( 'msg0', Bits8 ),
                                         ( 'msg1', Bits8 ) ] )
  MsgType = mk_bit_struct( "MsgType", [( 'msg0', Bits8 ),
                                       ( 'msg1', Msg1Type ) ] )

  run_test_state_machine(
      RTL2CLWrapper( QueueRTL( MsgType ) ),
      QueueCL( 1 ),
      argument_strategy=[( 'enq.msg.msg0',
                           st.integers( min_value=100, max_value=100 ) ),
                         ( 'enq.msg.msg1.msg1',
                           st.integers( min_value=200, max_value=200 ) ) ] )

  # specify composite strategy directly
  run_test_state_machine(
      RTL2CLWrapper( QueueRTL( MsgType ) ),
      QueueCL( 1 ),
      argument_strategy=[( 'enq.msg.msg1',
                           get_strategy_from_type( Msg1Type ) ) ] )

  # Strategy for a field and its subfield are not allowed
  try:
    run_test_state_machine(
        RTL2CLWrapper( QueueRTL( MsgType ) ),
        QueueCL( 1 ),
        argument_strategy=[( 'enq.msg.msg1',
                             get_strategy_from_type( Msg1Type ) ),
                           ( 'enq.msg.msg1.msg1',
                             st.integers( min_value=200, max_value=200 ) ) ] )
    assert False
  except AssertionError as e:
    print( e )

  # must be strategy
  try:
    run_test_state_machine(
        RTL2CLWrapper( QueueRTL( MsgType ) ),
        QueueCL( 1 ),
        argument_strategy=[( 'enq.msg.msg1', 1 ) ] )
    assert False
  except TypeError as e:
    print( e )
