from pymtl import *
from collections import deque
from pclib.ifcs  import valrdy_to_str, ValRdyBundle, EnRdyBundle

class TestSource( Updates ):

  def __init__( s, Type, input_ ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!" 
    s.input_  = deque( input_ ) # deque.popleft() is faster

    s.default = Type()
    s.out     = ValRdyBundle( Type )

    @s.update_on_edge
    def up_src():
      if s.out.rdy and s.input_:  s.input_.popleft()
      s.out.val = len(s.input_) > 0
      s.out.msg = s.default if not s.input_ else s.input_[0]

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return s.out.line_trace()

class StreamSource( Updates ):

  def __init__( s, Type ):
    s.out = ValRdyBundle( Type )
    s.ts  = 0

    @s.update_on_edge
    def up_src():
      s.out.msg = Bits64( ((s.ts+95827*(s.ts&1))<<32) + s.ts+(19182)*(s.ts&1) )
      s.out.val = 1
      s.ts += 1

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return s.out.line_trace()

class TestSourceEnRdy( Updates ):

  def __init__( s, Type, input_ = [] ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!"
    s.input_ = deque( input_ ) # deque.popleft() is faster

    s.default = Type()
    s.out = EnRdyBundle( Type )

    @s.update
    def up_src():
      s.out.en  = Bits1( len(s.input_) > 0 ) & s.out.rdy
      s.out.msg = s.default if not s.input_ else s.input_[0]

      if s.out.en and s.input_:
        s.input_.popleft()

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return s.out.line_trace()
