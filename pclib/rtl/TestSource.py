from pymtl import *
from collections import deque
from pclib.valrdy import valrdy_to_str

class TestBasicSource( UpdateConnect ):

  def __init__( s, input_ ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!" 

    s.input_ = deque( input_ ) # deque.popleft() is faster
    s.out = OutVPort(int)

    @s.update
    def up_src():
      if not s.input_:
        s.out = 0
      else:
        s.out = s.input_.popleft()

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return "%s" % s.out

class TestSource( UpdateConnect ):

  def __init__( s, input_ = [] ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!" 

    s.input_ = deque( input_ ) # deque.popleft() is faster
    s.msg = OutVPort(int)
    s.en  = OutVPort(int)
    s.rdy = InVPort(int)

    @s.update
    def up_src():
      s.en  = len(s.input_) > 0 & s.rdy
      s.msg = 0 if not s.input_ else s.input_[0]
      
      if s.en and s.input_:
        s.input_.popleft()

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.en, s.rdy )
