from pymtl import *
from pclib.update import RegEn, Reg, Mux, RShifter, LShifter, Adder, ZeroComp
from pclib.valrdy import valrdy_to_str
from pclib.ifcs   import ValRdyBundle

A_MUX_SEL_NBITS      = 1
A_MUX_SEL_LSH        = 0
A_MUX_SEL_LD         = 1
A_MUX_SEL_X          = 0

B_MUX_SEL_NBITS      = 1
B_MUX_SEL_RSH        = 0
B_MUX_SEL_LD         = 1
B_MUX_SEL_X          = 0

RESULT_MUX_SEL_NBITS = 1
RESULT_MUX_SEL_ADD   = 0
RESULT_MUX_SEL_0     = 1
RESULT_MUX_SEL_X     = 0

ADD_MUX_SEL_NBITS    = 1
ADD_MUX_SEL_ADD      = 0
ADD_MUX_SEL_RESULT   = 1
ADD_MUX_SEL_X        = 0

class CalcShamt( UpdatesImpl ):

  def __init__( s ):
    s.in_ = ValuePort( Bits8 )
    s.out = ValuePort( Bits4 )
    @s.update
    def up_calc_shamt():
      if   not s.in_: s.out = Bits4( 8 )
      elif s.in_[0] : s.out = Bits4( 1 )
      elif s.in_[1] : s.out = Bits4( 1 )
      elif s.in_[2] : s.out = Bits4( 2 )
      elif s.in_[3] : s.out = Bits4( 3 )
      elif s.in_[4] : s.out = Bits4( 4 )
      elif s.in_[5] : s.out = Bits4( 5 )
      elif s.in_[6] : s.out = Bits4( 6 )
      elif s.in_[7] : s.out = Bits4( 7 )

class IntMulCS( PortBundle ):

  def __init__( s ):
    s.a_mux_sel   = ValuePort( Bits1 )
    s.b_mux_sel   = ValuePort( Bits1 )
    s.res_mux_sel = ValuePort( Bits1 )
    s.res_reg_en  = ValuePort( Bits1 )
    s.add_mux_sel = ValuePort( Bits1 )
    s.b_lsb       = ValuePort( Bits1 )
    s.is_b_zero   = ValuePort( Bits1 )

class IntMulVarLatDpath( UpdatesImpl ):

  def __init__( s ):

    s.req_msg     = ValuePort( Bits64 )
    s.resp_msg    = ValuePort( Bits32 )
    s.cs          = IntMulCS()

    # Variables and upblks associated with B

    s.b_mux                    = Mux( Bits32, B_MUX_SEL_NBITS )
    s.b_mux.in_[B_MUX_SEL_LD] |= s.req_msg[32:64]
    s.b_mux.sel               |= s.cs.b_mux_sel

    s.b_reg         = Reg( Bits32 )
    s.b_reg.in_    |= s.b_mux.out
    s.cs.b_lsb     |= s.b_reg.out[0]

    s.calc_sh       = CalcShamt()
    s.calc_sh.in_  |= s.b_reg.out[0:8]

    s.b_zcp         = ZeroComp( Bits32 )
    s.b_zcp.in_    |= s.b_reg.out
    s.b_zcp.out    |= s.cs.is_b_zero

    s.b_rsh         = RShifter( Bits32, 4 )
    s.b_rsh.in_    |= s.b_reg.out
    s.b_rsh.shamt  |= s.calc_sh.out
    s.b_rsh.out    |= s.b_mux.in_[B_MUX_SEL_RSH]

    # Variables and upblks associated with A

    s.a_mux                    = Mux( Bits32, A_MUX_SEL_NBITS )
    s.a_mux.in_[A_MUX_SEL_LD] |= s.req_msg[0:32]
    s.a_mux.sel               |= s.cs.a_mux_sel

    s.a_reg         = Reg( Bits32 )
    s.a_reg.in_    |= s.a_mux.out

    s.a_lsh         = LShifter( Bits32, 4 )
    s.a_lsh.in_    |= s.a_reg.out
    s.a_lsh.shamt  |= s.calc_sh.out
    s.a_lsh.out    |= s.a_mux.in_[A_MUX_SEL_LSH]

    # Variables and upblks associated with Result

    s.res_mux                        = Mux( Bits32, RESULT_MUX_SEL_NBITS )
    s.res_mux.in_[RESULT_MUX_SEL_0]  = Bits32(0)
    s.res_mux.sel                   |= s.cs.res_mux_sel

    s.res_reg       = RegEn( Bits32 )
    s.res_reg.en   |= s.cs.res_reg_en
    s.res_reg.in_  |= s.res_mux.out
    s.res_reg.out  |= s.resp_msg

    s.res_add       = Adder( Bits32 )
    s.res_add.in0  |= s.a_reg.out
    s.res_add.in1  |= s.res_reg.out

    s.add_mux                          = Mux( Bits32, ADD_MUX_SEL_NBITS )
    s.add_mux.in_[ADD_MUX_SEL_ADD   ] |= s.res_add.out
    s.add_mux.in_[ADD_MUX_SEL_RESULT] |= s.res_reg.out
    s.add_mux.sel                     |= s.cs.add_mux_sel
    s.add_mux.out                     |= s.res_mux.in_[RESULT_MUX_SEL_ADD]

class IntMulVarLatCtrl( UpdatesImpl ):

  def __init__( s ):

    s.req_val  = ValuePort( Bits1 )
    s.req_rdy  = ValuePort( Bits1 )
    s.resp_val = ValuePort( Bits1 )
    s.resp_rdy = ValuePort( Bits1 )
    s.cs       = IntMulCS()

    s.state = Reg( Bits2 )

    s.STATE_IDLE = 0
    s.STATE_CALC = 1
    s.STATE_DONE = 2

    @s.update
    def state_transitions():

      curr_state = s.state.out

      if   curr_state == s.STATE_IDLE:
        if s.req_val and s.req_rdy:
          s.state.in_ = s.STATE_CALC

      elif curr_state == s.STATE_CALC:
        if s.cs.is_b_zero:
          s.state.in_ = s.STATE_DONE

      elif curr_state == s.STATE_DONE:
        if s.resp_val and s.resp_rdy:
          s.state.in_ = s.STATE_IDLE

    @s.update
    def state_outputs():

      curr_state = s.state.out

      s.req_rdy        = Bits1( 0 )
      s.resp_val       = Bits1( 0 )
      s.cs.a_mux_sel   = Bits1( 0 )
      s.cs.b_mux_sel   = Bits1( 0 )
      s.cs.add_mux_sel = Bits1( 0 )
      s.cs.res_mux_sel = Bits1( 0 )
      s.cs.res_reg_en  = Bits1( 0 )

      # In IDLE state we simply wait for inputs to arrive and latch them

      if curr_state == s.STATE_IDLE:
        s.req_rdy        = Bits1( 1 )
        s.resp_val       = Bits1( 0 )

        s.cs.a_mux_sel   = Bits1( A_MUX_SEL_LD )
        s.cs.b_mux_sel   = Bits1( B_MUX_SEL_LD )
        s.cs.res_mux_sel = Bits1( RESULT_MUX_SEL_0 )
        s.cs.res_reg_en  = Bits1( 1 )
        s.cs.add_mux_sel = Bits1( ADD_MUX_SEL_X )

      elif curr_state == s.STATE_CALC:
        s.req_rdy        = Bits1( 0 )
        s.resp_val       = Bits1( 0 )

        s.cs.a_mux_sel   = Bits1( A_MUX_SEL_LSH )
        s.cs.b_mux_sel   = Bits1( B_MUX_SEL_RSH )
        s.cs.res_mux_sel = Bits1( RESULT_MUX_SEL_ADD )
        s.cs.res_reg_en  = Bits1( 1 )
        s.cs.add_mux_sel = Bits1( ADD_MUX_SEL_ADD ) if s.cs.b_lsb else Bits1( ADD_MUX_SEL_RESULT )

      # In DONE state we simply wait for output transaction to occur

      elif curr_state == s.STATE_DONE:
        s.req_rdy        = Bits1( 0 )
        s.resp_val       = Bits1( 1 )

        s.cs.a_mux_sel   = Bits1( A_MUX_SEL_X )
        s.cs.b_mux_sel   = Bits1( A_MUX_SEL_X )
        s.cs.res_mux_sel = Bits1( A_MUX_SEL_X )
        s.cs.add_mux_sel = Bits1( A_MUX_SEL_X )
        s.cs.res_reg_en  = Bits1( 0 )

class IntMulVarLat( UpdatesImpl ):

  def __init__( s ):

    s.req  = ValRdyBundle( Bits64 )
    s.resp = ValRdyBundle( Bits32 )

    s.dpath     = IntMulVarLatDpath()
    s.ctrl      = IntMulVarLatCtrl()
    s.dpath.cs |= s.ctrl.cs

    s.req.val  |= s.ctrl.req_val
    s.req.rdy  |= s.ctrl.req_rdy
    s.req.msg  |= s.dpath.req_msg

    s.resp.val |= s.ctrl.resp_val
    s.resp.rdy |= s.ctrl.resp_rdy
    s.resp.msg |= s.dpath.resp_msg

  def line_trace( s ):
    return s.dpath.a_reg.line_trace() + s.dpath.res_reg.line_trace()

if __name__ == "__main__":

  from pclib.test import TestSourceValRdy, TestSinkValRdy
  import random

  class TestHarness( UpdatesImpl ):

    def __init__( s, model, src_msgs, sink_msgs ):

      s.src  = TestSourceValRdy( Bits64, src_msgs )
      s.imul = model
      s.sink = TestSinkValRdy( Bits32, sink_msgs )

      s.imul.req  |= s.src.out
      s.imul.resp |= s.sink.in_

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace()+" >>> "+s.imul.line_trace()+" >>> "+s.sink.line_trace()

  random.seed(0xdeadbeef)
  src_msgs  = []
  sink_msgs = []

  for i in xrange(20):
    x = random.randint(0, 100)
    y = random.randint(0, 100)
    z = Bits64(0)
    z[0:32]  = x
    z[32:64] = y
    src_msgs.append( z )
    sink_msgs.append( Bits32( x * y ) )

  th = TestHarness( IntMulVarLat(), src_msgs, sink_msgs )
  th.elaborate()
  th.print_c_schedule()
  while not th.done():
    th.cycle()
    print th.line_trace()
