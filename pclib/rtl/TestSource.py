from pymtl import *
from collections import deque
from pclib.valrdy import valrdy_to_str
from pclib.ifcs   import OutValRdyIfc

class TestBasicSource( ComponentLevel3 ):

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

class TestSourceValRdy( ComponentLevel3 ):

  def __init__( s, Type, input_ ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!" 

    s.input_  = deque( input_ ) # deque.popleft() is faster
    s.default = Type( 0 )
    s.out     = OutValRdyIfc( Type )

    @s.update_on_edge
    def up_src():
      if s.out.rdy and s.input_:  s.input_.popleft()
      s.out.val = Bits1( len(s.input_) > 0 )
      s.out.msg = s.default if not s.input_ else s.input_[0]

    # The following is equivalent
    # @s.update
    # def up_src_val():
      # if not s.input_:
        # s.msg = [0] * nmsgs
        # s.val = 0
      # else:
        # s.msg = s.input_[0]
        # s.val = 1

    # @s.update
    # def up_src_rdy():
      # if s.rdy and s.input_:
        # s.input_.popleft()

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return s.out.line_trace()

class TestSource( ComponentLevel3 ):

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
