from pymtl import *
from collections import deque
from pclib.valrdy import valrdy_to_str
from ValRdyBundle import ValRdyBundle

class TestSource( Updates ):

  def __init__( s, type_, input_ ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!" 

    s.input_  = deque( input_ ) # deque.popleft() is faster
    s.default = type_( 0 )
    s.out     = ValRdyBundle( type_ )

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

  def __init__( s, type_ ):
    s.out = ValRdyBundle( nmsgs )
    s.ts  = 0

    @s.update_on_edge
    def up_src():
      s.out.msg = ( s.ts+95827*(s.ts&1), s.ts+(19182)*(s.ts&1) )
      # s.msg = ( 60, 35 )
      s.out.val = 1
      s.ts += 1

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return s.out.line_trace()
