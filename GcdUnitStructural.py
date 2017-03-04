from pymtl import *
from pclib import RegEn, Reg, Mux

A_MUX_SEL_IN    = 0
A_MUX_SEL_SUB   = 1
A_MUX_SEL_B     = 2
A_MUX_SEL_X     = 0

B_MUX_SEL_A     = 0
B_MUX_SEL_IN    = 1
B_MUX_SEL_X     = 0

class GcdUnitDpath( MethodComponent ):

  def __init__( s ):

    s.req_msg_a = s.req_msg_b = 0

    s.a_mux_sel = s.a_reg_en  = 0
    s.b_mux_sel = s.b_reg_en  = 0

    s.a_reg = RegEn()
    s.b_reg = RegEn()

    s.a_mux = Mux(3)
    s.b_mux = Mux(2)

    s.sub_out = 0

    @s.update
    def up_connect_to_a_mux():
      s.a_mux.in_[A_MUX_SEL_IN]  = s.req_msg_a
      s.a_mux.in_[A_MUX_SEL_SUB] = s.sub_out
      s.a_mux.in_[A_MUX_SEL_B]   = s.b_reg.rd()
      s.a_mux.sel = s.a_mux_sel

    @s.update
    def up_connect_from_a_mux():
      s.a_reg.wr( s.a_mux.out )

    @s.update
    def up_connect_to_b_mux():
      s.b_mux.in_[B_MUX_SEL_A]  = s.a_reg.rd()
      s.b_mux.in_[B_MUX_SEL_IN] = s.req_msg_b
      s.b_mux.sel = s.b_mux_sel

    @s.update
    def up_connect_from_b_mux():
      s.b_reg.wr( s.b_mux.out )

    @s.update
    def up_regs_enable():
      s.a_reg.enable( s.a_reg_en )
      s.b_reg.enable( s.b_reg_en )

    s.is_b_zero = s.is_a_lt_b = 0

    @s.update
    def up_comparisons():
      s.is_b_zero = ( s.b_reg.rd() == 0 )
      s.is_a_lt_b = ( s.a_reg.rd() < s.b_reg.rd() )

    s.resp_msg  = 0

    @s.update
    def up_subtract():
      s.sub_out = s.resp_msg = s.a_reg.rd() - s.b_reg.rd()

class GcdUnitCtrl( MethodComponent ):

  def __init__( s ):

    s.req_val  = s.req_rdy = 0
    s.resp_val = s.resp_rdy = 0

    s.state = Reg()

    s.STATE_IDLE = 0
    s.STATE_CALC = 1
    s.STATE_DONE = 2

    s.is_b_zero = s.is_a_lt_b = 0
    s.a_mux_sel = s.a_reg_en  = 0
    s.b_mux_sel = s.b_reg_en  = 0

    @s.update
    def state_transitions():

      curr_state = s.state.rd()

      if   curr_state == s.STATE_IDLE:
        if s.req_val and s.req_rdy:
          s.state.wr( s.STATE_CALC )

      elif curr_state == s.STATE_CALC:
        if not s.is_a_lt_b and s.is_b_zero:
          s.state.wr( s.STATE_DONE )

      elif curr_state == s.STATE_DONE:
        if s.resp_val and s.resp_rdy:
          s.state.wr( s.STATE_IDLE )

    s.do_swap = s.do_sub  = 0

    @s.update
    def state_outputs():

      curr_state = s.state.rd()

      s.do_swap   = s.do_sub = 0
      s.req_rdy   = s.resp_val = 0
      s.a_mux_sel = s.a_reg_en = 0
      s.b_mux_sel = s.b_reg_en  = 0

      # In IDLE state we simply wait for inputs to arrive and latch them

      if curr_state == s.STATE_IDLE:
        s.req_rdy   = 1
        s.resp_val  = 0

        s.a_mux_sel = A_MUX_SEL_IN
        s.b_mux_sel = B_MUX_SEL_IN
        s.a_reg_en  = s.b_reg_en  = 1

      # In CALC state we iteratively swap/sub to calculate GCD

      elif curr_state == s.STATE_CALC:

        s.do_swap = s.is_a_lt_b
        s.do_sub  = ~s.is_b_zero

        s.req_rdy   = s.resp_val  = 0
        s.a_mux_sel = A_MUX_SEL_B if s.do_swap else A_MUX_SEL_SUB
        s.a_reg_en  = 1
        s.b_mux_sel = B_MUX_SEL_A
        s.b_reg_en  = s.do_swap

      # In DONE state we simply wait for output transaction to occur

      elif curr_state == s.STATE_DONE:
        s.req_rdy   = 0
        s.resp_val  = 1
        s.a_mux_sel = s.b_mux_sel = A_MUX_SEL_X
        s.a_reg_en  = s.b_reg_en = 0

class GcdUnit( MethodComponent ):

  def __init__( s ):

    s.req_rdy = s.req_val = s.req_msg_a = s.req_msg_b = 0
    s.resp_rdy = s.resp_val = s.resp_msg = 0

    s.dpath = GcdUnitDpath()
    s.ctrl  = GcdUnitCtrl()

    @s.update
    def up_connect_valrdy():
      s.ctrl.req_val    = s.req_val
      s.req_rdy         = s.ctrl.req_rdy
      s.dpath.req_msg_a = s.req_msg_a
      s.dpath.req_msg_b = s.req_msg_b

      s.resp_val        = s.ctrl.resp_val
      s.ctrl.resp_rdy   = s.resp_rdy
      s.resp_msg        = s.dpath.resp_msg

    @s.update
    def up_connect_dpath(): # ctrl signals
      s.dpath.a_mux_sel = s.ctrl.a_mux_sel
      s.dpath.b_mux_sel = s.ctrl.b_mux_sel

      s.dpath.a_reg_en  = s.ctrl.a_reg_en
      s.dpath.b_reg_en  = s.ctrl.b_reg_en

    @s.update
    def up_connect_ctrl(): # status signals
      s.ctrl.is_b_zero  = s.dpath.is_b_zero
      s.ctrl.is_a_lt_b  = s.dpath.is_a_lt_b

A = GcdUnit()
A.elaborate()
A.print_schedule()

A.req_val = 1
A.resp_rdy = 1

for cycle in xrange(10):
  A.req_msg_a, A.req_msg_b = cycle+95827*(cycle&1), cycle+(19182)*(cycle&1)
  # A.req_msg_a, A.req_msg_b = 60,35
  A.cycle()
  # print "req val:%d rdy:%d a:%d b:%d" % (A.req_val, A.req_rdy, A.req_msg_a, A.req_msg_b), \
        # A.dpath.a_reg.line_trace(), A.dpath.b_reg.line_trace(), \
        # "resp val:%d rdy:%d gcd:%d" % (A.resp_val, A.resp_rdy, A.resp_msg )
