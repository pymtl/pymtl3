from pymtl import *
from collections import deque
from pclib.valrdy import valrdy_to_str
from pclib.ifcs   import OutValRdyIfc

class TestBasicSource( RTLComponent ):

  def __init__( s, Type, input_ ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!" 

    s.Type = Type
    s.input_ = deque( input_ ) # deque.popleft() is faster
    s.out = OutVPort( Type )

    @s.update
    def up_src():
      if not s.input_:
        s.out = s.Type()
      else:
        s.out = s.input_.popleft()

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return "%s" % s.out

class TestSourceValRdy( RTLComponent ):

  def __init__( s, Type, msgs ):
    assert type(msgs) == list, "TestSrc only accepts a list of inputs!" 

    s.msgs    = msgs
    s.src_msgs = deque( msgs )
    s.default = Type()
    s.out     = OutValRdyIfc( Type )

    @s.update_on_edge
    def up_src():
      if s.reset:
        s.out.val  = Bits1(0)
        s.src_msgs = deque( s.msgs )
      else:
        if (s.out.rdy & s.out.val) and s.src_msgs:
          s.src_msgs.popleft()
        s.out.val = Bits1( len(s.src_msgs) > 0 )
        s.out.msg = s.default if not s.src_msgs else s.src_msgs[0]

  def done( s ):
    return not s.src_msgs

  def line_trace( s ):
    return s.out.line_trace()

class TestSource( RTLComponent ):

  def __init__( s, Type, input_ = [] ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!" 

    s.Type = Type
    s.input_ = deque( input_ ) # deque.popleft() is faster

    s.msg = OutVPort( Type )
    s.en  = OutVPort( Type )
    s.rdy = InVPort( Type )

    @s.update
    def up_src():
      s.en  = len(s.input_) > 0 & s.rdy
      s.msg = s.Type() if not s.input_ else s.input_[0]
      
      if s.en and s.input_:
        s.input_.popleft()

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.en, s.rdy )
