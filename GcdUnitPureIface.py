from pymtl import *
from pclib.method import Mux
from pclib.interface import RegEn, Reg, Port, Subtractor

A_MUX_SEL_IN    = 0
A_MUX_SEL_SUB   = 1
A_MUX_SEL_B     = 2
A_MUX_SEL_X     = 0

B_MUX_SEL_A     = 0
B_MUX_SEL_IN    = 1
B_MUX_SEL_X     = 0

class GcdUnitDpath( MethodComponent ):

  def __init__( s ):

    s.req_msg_a = Port(int)
    s.req_msg_b = Port(int)
    s.resp_msg  = Port(int)

    s.a_mux_sel = Port(int)
    s.a_reg_en  = Port(int)
    s.b_mux_sel = Port(int)
    s.b_reg_en  = Port(int)

    s.a_reg = RegEn()
    s.a_reg.en |= s.a_reg_en

    s.b_reg = RegEn()
    s.b_reg.en |= s.b_reg_en

    s.sub = Subtractor()
    s.sub.in0 |= s.a_reg.out
    s.sub.in1 |= s.b_reg.out
    s.sub.out |= s.resp_msg

    s.a_mux = Mux(3)
    s.b_mux = Mux(2)

    @s.update
    def up_connect_to_a_mux():
      s.a_mux.in_[A_MUX_SEL_IN]  = s.req_msg_a.rd()
      s.a_mux.in_[A_MUX_SEL_SUB] = s.sub.out.rd()
      s.a_mux.in_[A_MUX_SEL_B]   = s.b_reg.out.rd()
      s.a_mux.sel                = s.a_mux_sel.rd()

    @s.update
    def up_connect_from_a_mux():
      s.a_reg.in_.wr( s.a_mux.out )

    @s.update
    def up_connect_to_b_mux():
      s.b_mux.in_[B_MUX_SEL_A]  = s.a_reg.out.rd()
      s.b_mux.in_[B_MUX_SEL_IN] = s.req_msg_b.rd()
      s.b_mux.sel               = s.b_mux_sel.rd()

    @s.update
    def up_connect_from_b_mux():
      s.b_reg.in_.wr( s.b_mux.out )

    # s.a_mux = Mux(3)
    # s.a_mux.sel               |= s.a_mux_sel
    # s.a_mux.in_[A_MUX_SEL_IN] |= s.req_msg_a
    # s.a_mux.in_[A_MUX_SEL_SUB]|= s.sub.out

    # s.b_mux = Mux(2)
    # s.b_mux.sel               |= s.b_mux_sel
    # s.b_mux.in_[B_MUX_SEL_IN] |= s.req_msg_b

    # @s.update
    # def up_connect_to_a_mux():
      # s.a_mux.in_[A_MUX_SEL_B] = s.b_reg.rd()

    # @s.update
    # def up_connect_from_a_mux():
      # s.a_reg.wr( s.a_mux.out )

    # @s.update
    # def up_connect_to_b_mux():
      # s.b_mux.in_[B_MUX_SEL_A] = s.a_reg.rd()

    # @s.update
    # def up_connect_from_b_mux():
      # s.b_reg.wr( s.b_mux.out )

    s.is_b_zero = Port(int)
    s.is_a_lt_b = Port(int)

    @s.update
    def up_comparisons():
      s.is_b_zero.wr( s.b_reg.out.rd() == 0 )
      s.is_a_lt_b.wr( s.a_reg.out.rd() < s.b_reg.out.rd() )


class GcdUnitCtrl( MethodComponent ):

  def __init__( s ):

    s.req_val  = Port(int)
    s.req_rdy  = Port(int)
    s.resp_val = Port(int)
    s.resp_rdy = Port(int)

    s.state = Reg()

    s.STATE_IDLE = 0
    s.STATE_CALC = 1
    s.STATE_DONE = 2

    s.is_b_zero = Port(int)
    s.is_a_lt_b = Port(int)
    s.a_mux_sel = Port(int)
    s.a_reg_en  = Port(int)
    s.b_mux_sel = Port(int)
    s.b_reg_en  = Port(int)

    @s.update
    def state_transitions():

      curr_state = s.state.out.rd()

      if   curr_state == s.STATE_IDLE:
        if s.req_val.rd() and s.req_rdy.rd():
          s.state.in_.wr( s.STATE_CALC )

      elif curr_state == s.STATE_CALC:
        if not s.is_a_lt_b.rd() and s.is_b_zero.rd():
          s.state.in_.wr( s.STATE_DONE )

      elif curr_state == s.STATE_DONE:
        if s.resp_val.rd() and s.resp_rdy.rd():
          s.state.in_.wr( s.STATE_IDLE )

    s.do_swap = s.do_sub  = 0

    @s.update
    def state_outputs():

      curr_state = s.state.out.rd()

      s.do_swap = s.do_sub = 0
      s.req_rdy  .wr( 0 )
      s.resp_val .wr( 0 )
      s.a_mux_sel.wr( 0 )
      s.a_reg_en .wr( 0 )
      s.b_mux_sel.wr( 0 )
      s.b_reg_en .wr( 0 )

      # In IDLE state we simply wait for inputs to arrive and latch them

      if curr_state == s.STATE_IDLE:
        s.req_rdy .wr( 1 )
        s.resp_val.wr( 0 )

        s.a_mux_sel.wr( A_MUX_SEL_IN )
        s.b_mux_sel.wr( B_MUX_SEL_IN )
        s.a_reg_en .wr( 1 )
        s.b_reg_en .wr( 1 )

      # In CALC state we iteratively swap/sub to calculate GCD

      elif curr_state == s.STATE_CALC:

        s.do_swap = s.is_a_lt_b.rd()
        s.do_sub  = ~s.is_b_zero.rd()

        s.req_rdy  .wr( 0 )
        s.resp_val .wr( 0 )
        s.a_mux_sel.wr( A_MUX_SEL_B if s.do_swap else A_MUX_SEL_SUB )
        s.a_reg_en .wr( 1 )
        s.b_mux_sel.wr( B_MUX_SEL_A )
        s.b_reg_en .wr( s.do_swap )

      # In DONE state we simply wait for output transaction to occur

      elif curr_state == s.STATE_DONE:
        s.req_rdy  .wr( 0 )
        s.resp_val .wr( 1 )
        s.a_mux_sel.wr( A_MUX_SEL_X )
        s.b_mux_sel.wr( B_MUX_SEL_X )
        s.a_reg_en .wr( 0 )
        s.b_reg_en .wr( 0 )

class GcdUnit( MethodComponent ):

  def __init__( s ):

    s.req_rdy   = Port(int)
    s.req_val   = Port(int)
    s.req_msg_a = Port(int)
    s.req_msg_b = Port(int)
    s.resp_rdy  = Port(int)
    s.resp_val  = Port(int)
    s.resp_msg  = Port(int)

    s.dpath = GcdUnitDpath()
    s.ctrl  = GcdUnitCtrl()

    s.ctrl.req_val    |= s.req_val
    s.ctrl.req_rdy    |= s.req_rdy
    s.dpath.req_msg_a |= s.req_msg_a
    s.dpath.req_msg_b |= s.req_msg_b

    s.ctrl.resp_val   |= s.resp_val
    s.ctrl.resp_rdy   |= s.resp_rdy
    s.dpath.resp_msg  |= s.resp_msg

    s.dpath.a_mux_sel |= s.ctrl.a_mux_sel
    s.dpath.b_mux_sel |= s.ctrl.b_mux_sel

    s.dpath.a_reg_en  |= s.ctrl.a_reg_en
    s.dpath.b_reg_en  |= s.ctrl.b_reg_en

    s.ctrl.is_b_zero  |= s.dpath.is_b_zero
    s.ctrl.is_a_lt_b  |= s.dpath.is_a_lt_b

  def line_trace( s ):
    return "{} {} {}".format( A.dpath.a_reg.line_trace(), \
                              A.dpath.b_reg.line_trace(), \
                              A.dpath.sub.line_trace() )

A = GcdUnit()
A.elaborate()
A.print_schedule()

A.req_val .wr( 1 )
A.resp_rdy.wr( 1 )

for cycle in xrange(10):
  A.req_msg_a.wr( cycle+95827*(cycle&1) )
  A.req_msg_b.wr( cycle+(19182)*(cycle&1) )
  # A.req_msg_a.wr(60)
  # A.req_msg_b.wr(35)
  A.cycle()
  # print "req val:%s rdy:%s a:%s b:%s" % (A.req_val.line_trace(), A.req_rdy.line_trace(), A.req_msg_a.line_trace(), A.req_msg_b.line_trace()), \
        # A.line_trace(), \
        # "resp val:%s rdy:%s gcd:%s" % (A.resp_val.line_trace(), A.resp_rdy.line_trace(), A.resp_msg.line_trace() )
