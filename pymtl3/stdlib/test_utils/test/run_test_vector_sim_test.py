#=========================================================================
# run_test_vector_sim_test
#=========================================================================

import pytest

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim
from pymtl3.stdlib.test_utils import RunTestVectorSimError

#-------------------------------------------------------------------------
# Test component with 1 input and 1 output port
#-------------------------------------------------------------------------

class TestComponent1i1o( Component ):
  def construct( s ):
    s.in_ = InPort(2)
    s.out = OutPort(2)

    @update
    def up():
      s.out @= s.in_ + 1

  def line_trace(s):
    return f"{s.in_}(){s.out}"

def test_1i1o_basic( cmdline_opts ):
  run_test_vector_sim( TestComponent1i1o(), [
    ('in_ out*' ),
    [ 0,  1     ],
    [ 1,  2     ],
    [ 0,  1     ],
  ], cmdline_opts )

# Verify that using a don't care works

def test_1i1o_dontcare( cmdline_opts ):
  run_test_vector_sim( TestComponent1i1o(), [
    ('in_ out*' ),
    [ 0,  '?'   ],
    [ 1,  2     ],
    [ 0,  1     ],
  ], cmdline_opts )

# Verify that an exception is thrown if the output is incorrect

def test_1i1o_incorrect_output( cmdline_opts ):
  with pytest.raises(RunTestVectorSimError):
    run_test_vector_sim( TestComponent1i1o(), [
      ('in_ out*' ),
      [ 0,  0     ],
      [ 1,  1     ],
      [ 0,  0     ],
    ], cmdline_opts )

# Verify that an exception is thrown if input port name is wrong

def test_1i1o_incorrect_inport( cmdline_opts ):
  with pytest.raises(RunTestVectorSimError):
    run_test_vector_sim( TestComponent1i1o(), [
      ('inX out*' ),
      [ 0,  0     ],
      [ 1,  2     ],
      [ 0,  0     ],
    ], cmdline_opts )

# Verify that an exception is thrown if output port name is wrong

def test_1i1o_incorrect_outport( cmdline_opts ):
  with pytest.raises(RunTestVectorSimError):
    run_test_vector_sim( TestComponent1i1o(), [
      ('in_ outX*' ),
      [ 0,  0      ],
      [ 1,  2      ],
      [ 0,  0      ],
    ], cmdline_opts )

#-------------------------------------------------------------------------
# Test component with 2 input and 2 output port
#-------------------------------------------------------------------------

class TestComponent2i2o( Component ):
  def construct( s ):
    s.in0  = InPort(2)
    s.in1  = InPort(2)
    s.out0 = OutPort(2)
    s.out1 = OutPort(2)

    @update
    def up():
      s.out0 @= s.in0 + 1
      s.out1 @= s.in1 + 2

  def line_trace(s):
    return f"{s.in0}|{s.in1}(){s.out0}|{s.out1}"

def test_2i2o_basic( cmdline_opts ):
  run_test_vector_sim( TestComponent2i2o(), [
    ('in0 in1 out0* out1*' ),
    [ 0,  0,  1,    2      ],
    [ 1,  0,  2,    2      ],
    [ 0,  1,  1,    3      ],
  ], cmdline_opts )

# Verify that using a don't care works

def test_2i2o_dontcare( cmdline_opts ):
  run_test_vector_sim( TestComponent2i2o(), [
    ('in0 in1 out0* out1*' ),
    [ 0,  0,  '?',  '?'    ],
    [ 1,  0,  2,    '?'    ],
    [ 0,  1,  1,    3      ],
  ], cmdline_opts )

# Verify that an exception is thrown if the output is incorrect

def test_2i2o_incorrect_output( cmdline_opts ):
  with pytest.raises(RunTestVectorSimError):
    run_test_vector_sim( TestComponent2i2o(), [
      ('in0 in1 out0* out1*' ),
      [ 0,  0,  1,    2      ],
      [ 1,  0,  3,    2      ],
      [ 0,  1,  1,    3      ],
    ], cmdline_opts )

# Verify that an exception is thrown if input port name is wrong

def test_2i2o_incorrect_inport( cmdline_opts ):
  with pytest.raises(RunTestVectorSimError):
    run_test_vector_sim( TestComponent2i2o(), [
      ('in0 inX out0* out1*' ),
      [ 0,  0,  1,    2      ],
      [ 1,  0,  2,    2      ],
      [ 0,  1,  1,    3      ],
    ], cmdline_opts )

# Verify that an exception is thrown if output port name is wrong

def test_2i2o_incorrect_outport( cmdline_opts ):
  with pytest.raises(RunTestVectorSimError):
    run_test_vector_sim( TestComponent2i2o(), [
      ('in0 in1 outX* out1*' ),
      [ 0,  0,  1,    2      ],
      [ 1,  0,  2,    2      ],
      [ 0,  1,  1,    3      ],
    ], cmdline_opts )

#-------------------------------------------------------------------------
# Test component with input and output array ports
#-------------------------------------------------------------------------

class TestComponentArray2i2o( Component ):
  def construct( s ):
    s.in_  = [ InPort(2)  for _ in range(2) ]
    s.out  = [ OutPort(2) for _ in range(2) ]

    @update
    def up():
      s.out[0] @= s.in_[0] + 1
      s.out[1] @= s.in_[1] + 2

  def line_trace(s):
    return f"{s.in_[0]}|{s.in_[1]}(){s.out[0]}|{s.out[1]}"

def test_a2i2o_basic( cmdline_opts ):
  run_test_vector_sim( TestComponentArray2i2o(), [
    ('in_[0] in_[1] out[0]* out[1]*' ),
    [ 0,     0,     1,      2        ],
    [ 1,     0,     2,      2        ],
    [ 0,     1,     1,      3        ],
  ], cmdline_opts )

# Verify that using a don't care works

def test_a2i2o_dontcare( cmdline_opts ):
  run_test_vector_sim( TestComponentArray2i2o(), [
    ('in_[0] in_[1] out[0]* out[1]*' ),
    [ 0,     0,     '?',    '?'      ],
    [ 1,     0,     2,      '?'      ],
    [ 0,     1,     1,      3        ],
  ], cmdline_opts )

# Verify that an exception is thrown if the output is incorrect

def test_a2i2o_incorrect_output( cmdline_opts ):
  with pytest.raises(RunTestVectorSimError):
    run_test_vector_sim( TestComponentArray2i2o(), [
      ('in_[0] in_[1] out[0]* out[1]*' ),
      [ 0,     0,     1,      2        ],
      [ 1,     0,     3,      2        ],
      [ 0,     1,     1,      3        ],
    ], cmdline_opts )

# Verify that an exception is thrown if input port name is wrong

def test_a2i2o_incorrect_inport( cmdline_opts ):
  with pytest.raises(RunTestVectorSimError):
    run_test_vector_sim( TestComponentArray2i2o(), [
      ('in_[0] inX    out[0]* out[1]*' ),
      [ 0,     0,     1,      2        ],
      [ 1,     0,     2,      2        ],
      [ 0,     1,     1,      3        ],
    ], cmdline_opts )

# Verify that an exception is thrown if output port name is wrong

def test_a2i2o_incorrect_outport( cmdline_opts ):
  with pytest.raises(RunTestVectorSimError):
    run_test_vector_sim( TestComponentArray2i2o(), [
      ('in_[0] in_[1] outX*   out[1]*' ),
      [ 0,     0,     1,      2        ],
      [ 1,     0,     2,      2        ],
      [ 0,     1,     1,      3        ],
    ], cmdline_opts )

