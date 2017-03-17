from pymtl import *
from pclib.update import RegEn, Reg, Mux, ZeroComp, LTComp, Subtractor
from pclib.update import TestSourceValRdy, TestSinkValRdy
from pclib.valrdy import valrdy_to_str

A_MUX_SEL_IN    = 0
A_MUX_SEL_SUB   = 1
A_MUX_SEL_B     = 2
A_MUX_SEL_X     = 0

B_MUX_SEL_A     = 0
B_MUX_SEL_IN    = 1
B_MUX_SEL_X     = 0

class GcdUnitDpath( Updates ):

  def __init__( s ):

    s.req_msg_a = ValuePort(int)
    s.req_msg_b = ValuePort(int)
    s.resp_msg  = ValuePort(int)
    s.a_mux_sel = ValuePort(int)
    s.a_reg_en  = ValuePort(int)
    s.b_mux_sel = ValuePort(int)
    s.b_reg_en  = ValuePort(int)
    s.is_b_zero = ValuePort(int)
    s.is_a_lt_b = ValuePort(int)
    s.sub_out   = Wire(int)

    s.a_reg = RegEn()
    s.a_reg.en |= s.a_reg_en

    s.b_reg = RegEn()
    s.b_reg.en |= s.b_reg_en

    s.a_mux = Mux(3)
    s.a_reg.in_                |= s.a_mux.out
    s.a_mux.in_[A_MUX_SEL_IN]  |= s.req_msg_a
    s.a_mux.in_[A_MUX_SEL_SUB] |= s.sub_out
    s.a_mux.in_[A_MUX_SEL_B]   |= s.b_reg.out
    s.a_mux.sel                |= s.a_mux_sel

    s.b_mux = Mux(2)
    s.b_reg.in_               |= s.b_mux.out
    s.b_mux.in_[B_MUX_SEL_A]  |= s.a_reg.out
    s.b_mux.in_[B_MUX_SEL_IN] |= s.req_msg_b
    s.b_mux.sel               |= s.b_mux_sel

    s.b_zcp = ZeroComp()
    s.b_zcp.in_ |= s.b_reg.out
    s.is_b_zero |= s.b_zcp.out

    s.b_ltc = LTComp()
    s.b_ltc.in0 |= s.a_reg.out
    s.b_ltc.in1 |= s.b_reg.out
    s.is_a_lt_b |= s.b_ltc.out

    s.b_sub = Subtractor()
    s.b_sub.in0 |= s.a_reg.out
    s.b_sub.in1 |= s.b_reg.out
    s.resp_msg  |= s.b_sub.out
    s.sub_out   |= s.b_sub.out

class GcdUnitCtrl( Updates ):

  def __init__( s ):

    s.req_val  = ValuePort(int)
    s.req_rdy  = ValuePort(int)
    s.resp_val = ValuePort(int)
    s.resp_rdy = ValuePort(int)

    s.state = Reg()

    s.STATE_IDLE = 0
    s.STATE_CALC = 1
    s.STATE_DONE = 2

    s.is_b_zero = ValuePort(int)
    s.is_a_lt_b = ValuePort(int)
    s.a_mux_sel = ValuePort(int)
    s.a_reg_en  = ValuePort(int)
    s.b_mux_sel = ValuePort(int)
    s.b_reg_en  = ValuePort(int)

    @s.update
    def state_transitions():

      curr_state = s.state.out

      if   curr_state == s.STATE_IDLE:
        if s.req_val and s.req_rdy:
          s.state.in_ = s.STATE_CALC

      elif curr_state == s.STATE_CALC:
        if not s.is_a_lt_b and s.is_b_zero:
          s.state.in_ = s.STATE_DONE

      elif curr_state == s.STATE_DONE:
        if s.resp_val and s.resp_rdy:
          s.state.in_ = s.STATE_IDLE

    @s.update
    def state_outputs():

      curr_state = s.state.out

      s.req_rdy   = s.resp_val = 0
      s.a_mux_sel = s.a_reg_en = 0
      s.b_mux_sel = s.b_reg_en = 0

      # In IDLE state we simply wait for inputs to arrive and latch them

      if curr_state == s.STATE_IDLE:
        s.req_rdy   = 1
        s.resp_val  = 0

        s.a_mux_sel = A_MUX_SEL_IN
        s.b_mux_sel = B_MUX_SEL_IN
        s.a_reg_en  = s.b_reg_en  = 1

      # In CALC state we iteratively swap/sub to calculate GCD

      elif curr_state == s.STATE_CALC:

        s.req_rdy   = s.resp_val  = 0
        s.a_mux_sel = A_MUX_SEL_B if s.is_a_lt_b else A_MUX_SEL_SUB
        s.a_reg_en  = 1
        s.b_mux_sel = B_MUX_SEL_A
        s.b_reg_en  = s.is_a_lt_b

      # In DONE state we simply wait for output transaction to occur

      elif curr_state == s.STATE_DONE:
        s.req_rdy   = 0
        s.resp_val  = 1
        s.a_mux_sel = s.b_mux_sel = A_MUX_SEL_X
        s.a_reg_en  = s.b_reg_en = 0

class GcdUnit( Updates ):

  def __init__( s ):

    s.req_rdy   = ValuePort(int)
    s.req_val   = ValuePort(int)
    s.req_msg_a = ValuePort(int)
    s.req_msg_b = ValuePort(int)
    s.resp_rdy  = ValuePort(int)
    s.resp_val  = ValuePort(int)
    s.resp_msg  = ValuePort(int)

    s.dpath = GcdUnitDpath()
    s.ctrl  = GcdUnitCtrl()

    s.ctrl.req_val    |= s.req_val
    s.req_rdy         |= s.ctrl.req_rdy
    s.dpath.req_msg_a |= s.req_msg_a
    s.dpath.req_msg_b |= s.req_msg_b

    s.resp_val        |= s.ctrl.resp_val
    s.resp_rdy        |= s.ctrl.resp_rdy
    s.resp_msg        |= s.dpath.resp_msg

    s.dpath.a_mux_sel |= s.ctrl.a_mux_sel
    s.dpath.b_mux_sel |= s.ctrl.b_mux_sel
    s.dpath.a_reg_en  |= s.ctrl.a_reg_en
    s.dpath.b_reg_en  |= s.ctrl.b_reg_en

    s.ctrl.is_b_zero  |= s.dpath.is_b_zero
    s.ctrl.is_a_lt_b  |= s.dpath.is_a_lt_b

  def line_trace( s ):
    return s.dpath.a_reg.line_trace() + s.dpath.b_reg.line_trace()

class TestHarness( Updates ):

  def __init__( s ):

    s.src  = TestSourceValRdy( 2, [ (60,35), (18,24), (195,43) ])
    s.gcd  = GcdUnit()
    s.sink = TestSinkValRdy( [ 5, 6, 1 ] )

    s.src.val    |= s.gcd.req_val
    s.src.rdy    |= s.gcd.req_rdy
    s.src.msg[0] |= s.gcd.req_msg_a
    s.src.msg[1] |= s.gcd.req_msg_b

    s.sink.val   |= s.gcd.resp_val
    s.sink.rdy   |= s.gcd.resp_rdy
    s.sink.msg   |= s.gcd.resp_msg

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.gcd.line_trace()+" >>> "+s.sink.line_trace()

if __name__ == "__main__":
  A = TestHarness()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()
