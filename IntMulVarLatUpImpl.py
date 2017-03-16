from pymtl import *
from pclib.update import RegEn, Reg, Mux, RShifter, LShifter, Adder, ZeroComp

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

class CalcShamt( Updates ):

  def __init__( s ):
    s.in_ = ValuePort(int)
    s.out = ValuePort(int)
    @s.update
    def up_calc_shamt():
      if   s.in_ == 0: s.out = 8
      elif s.in_ & 0b00000001 : s.out = 1
      elif s.in_ & 0b00000010 : s.out = 1
      elif s.in_ & 0b00000100 : s.out = 2
      elif s.in_ & 0b00001000 : s.out = 3
      elif s.in_ & 0b00010000 : s.out = 4
      elif s.in_ & 0b00100000 : s.out = 5
      elif s.in_ & 0b01000000 : s.out = 6
      elif s.in_ & 0b10000000 : s.out = 7

class IntMulVarLatDpath( Updates ):

  def __init__( s ):

    s.req_msg_a   = ValuePort(int)
    s.req_msg_b   = ValuePort(int)
    s.resp_msg    = ValuePort(int)
    s.a_mux_sel   = ValuePort(int)
    s.b_mux_sel   = ValuePort(int)
    s.res_mux_sel = ValuePort(int)
    s.res_reg_en  = ValuePort(int)
    s.add_mux_sel = ValuePort(int)

    # Variables and upblks associated with B

    s.b_mux = Mux( 2**ADD_MUX_SEL_NBITS )
    @s.update
    def up_to_bmux():
      s.b_mux.in_[B_MUX_SEL_RSH] = s.b_rsh.out
      s.b_mux.in_[B_MUX_SEL_LD]  = s.req_msg_b
      s.b_mux.sel = s.b_mux_sel

    s.b_reg = Reg()
    @s.update
    def up_from_bmux_to_breg():
      s.b_reg.in_ = s.b_mux.out

    s.calc_shamt = CalcShamt()
    s.b_zcp      = ZeroComp()

    @s.update
    def up_to_calc_shamt_zcp():
      s.calc_shamt.in_ = s.b_reg.out & 0xff
      s.b_zcp.in_      = s.b_reg.out

    s.is_b_zero  = ValuePort(int)
    s.b_lsb      = ValuePort(int)
    @s.update
    def up_from_zcp():
      s.is_b_zero = s.b_zcp.out

    s.b_rsh = RShifter( 32, 4 )
    @s.update
    def up_to_brsh():
      s.b_lsb       = s.b_reg.out & 1
      s.b_rsh.in_   = s.b_reg.out
      s.b_rsh.shamt = s.calc_shamt.out

    # Variables and upblks associated with A

    s.a_mux = Mux( 2**ADD_MUX_SEL_NBITS )
    @s.update
    def up_to_amux():
      s.a_mux.in_[A_MUX_SEL_LSH] = s.a_lsh.out
      s.a_mux.in_[A_MUX_SEL_LD]  = s.req_msg_a
      s.a_mux.sel = s.a_mux_sel

    s.a_reg = Reg()
    @s.update
    def up_from_amux_to_areg():
      s.a_reg.in_ = s.a_mux.out

    s.a_lsh = LShifter( 32, 4 )
    @s.update
    def up_to_alsh():
      s.a_lsh.in_   = s.a_reg.out
      s.a_lsh.shamt = s.calc_shamt.out

    # Variables and upblks associated with Result

    s.res_mux = Mux( 2**ADD_MUX_SEL_NBITS )
    @s.update
    def up_to_resmux():
      s.res_mux.in_[RESULT_MUX_SEL_ADD] = s.add_mux.out
      s.res_mux.in_[RESULT_MUX_SEL_0]   = 0
      s.res_mux.sel = s.res_mux_sel

    s.res_reg = RegEn()
    @s.update
    def up_to_resreg():
      s.res_reg.en  = s.res_reg_en
      s.res_reg.in_ = s.res_mux.out

    s.res_add = Adder( 32 )
    @s.update
    def up_to_adder():
      s.res_add.in_[0] = s.a_reg.out
      s.res_add.in_[1] = s.res_reg.out

    s.add_mux = Mux( 2**ADD_MUX_SEL_NBITS )
    @s.update
    def up_to_addmux_resp():
      s.add_mux.in_[ADD_MUX_SEL_ADD   ] = s.res_add.out
      s.add_mux.in_[ADD_MUX_SEL_RESULT] = s.resp_msg = s.res_reg.out
      s.add_mux.sel = s.add_mux_sel

class IntMulVarLatCtrl( Updates ):

  def __init__( s ):

    s.req_val  = ValuePort(int)
    s.req_rdy  = ValuePort(int)
    s.resp_val = ValuePort(int)
    s.resp_rdy = ValuePort(int)

    s.state = Reg()

    s.STATE_IDLE = 0
    s.STATE_CALC = 1
    s.STATE_DONE = 2

    s.is_b_zero   = ValuePort(int)
    s.b_lsb       = ValuePort(int)
    s.a_mux_sel   = ValuePort(int)
    s.b_mux_sel   = ValuePort(int)
    s.add_mux_sel = ValuePort(int)
    s.res_mux_sel = ValuePort(int)
    s.res_reg_en  = ValuePort(int)

    @s.update
    def state_transitions():

      curr_state = s.state.out

      if   curr_state == s.STATE_IDLE:
        if s.req_val and s.req_rdy:
          s.state.in_ = s.STATE_CALC

      elif curr_state == s.STATE_CALC:
        if s.is_b_zero:
          s.state.in_ = s.STATE_DONE

      elif curr_state == s.STATE_DONE:
        if s.resp_val and s.resp_rdy:
          s.state.in_ = s.STATE_IDLE

    @s.update
    def state_outputs():

      curr_state = s.state.out

      s.req_rdy   = s.resp_val = 0
      s.a_mux_sel = s.b_mux_sel = s.add_mux_sel = 0
      s.res_mux_sel = s.res_reg_en = 0

      # In IDLE state we simply wait for inputs to arrive and latch them

      if curr_state == s.STATE_IDLE:
        s.req_rdy   = 1
        s.resp_val  = 0

        s.a_mux_sel   = A_MUX_SEL_LD
        s.b_mux_sel   = B_MUX_SEL_LD
        s.res_mux_sel = RESULT_MUX_SEL_0
        s.res_reg_en  = 1
        s.add_mux_sel = ADD_MUX_SEL_X

      elif curr_state == s.STATE_CALC:
        s.req_rdy = s.resp_val  = 0

        s.a_mux_sel   = A_MUX_SEL_LSH
        s.b_mux_sel   = B_MUX_SEL_RSH
        s.res_mux_sel = RESULT_MUX_SEL_ADD
        s.res_reg_en  = 1
        s.add_mux_sel = ADD_MUX_SEL_ADD if s.b_lsb else ADD_MUX_SEL_RESULT

      # In DONE state we simply wait for output transaction to occur

      elif curr_state == s.STATE_DONE:
        s.req_rdy   = 0
        s.resp_val  = 1
        s.a_mux_sel = s.b_mux_sel = s.res_mux_sel = s.add_mux_sel = A_MUX_SEL_X
        s.res_reg_en = 0

class IntMulVarLat( Updates ):

  def __init__( s ):

    s.req_rdy   = ValuePort(int)
    s.req_val   = ValuePort(int)
    s.req_msg_a = ValuePort(int)
    s.req_msg_b = ValuePort(int)
    s.resp_rdy  = ValuePort(int)
    s.resp_val  = ValuePort(int)
    s.resp_msg  = ValuePort(int)

    s.dpath = IntMulVarLatDpath()
    s.ctrl  = IntMulVarLatCtrl()

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
      s.dpath.a_mux_sel   = s.ctrl.a_mux_sel
      s.dpath.b_mux_sel   = s.ctrl.b_mux_sel
      s.dpath.res_mux_sel = s.ctrl.res_mux_sel
      s.dpath.res_reg_en  = s.ctrl.res_reg_en
      s.dpath.add_mux_sel = s.ctrl.add_mux_sel

    @s.update
    def up_connect_ctrl(): # status signals
      s.ctrl.is_b_zero = s.dpath.is_b_zero
      s.ctrl.b_lsb     = s.dpath.b_lsb

A = IntMulVarLat()
A.elaborate()
A.print_schedule()

A.req_val = 1
A.resp_rdy = 1

for cycle in xrange(10000000):
  A.req_msg_a, A.req_msg_b = (cycle+2) & 0xffff, (cycle+19182) & 0xffff
  # A.req_msg_a, A.req_msg_b = 60,35
  A.cycle()
  # print "req val:%d rdy:%d a:%d b:%d" % (A.req_val, A.req_rdy, A.req_msg_a, A.req_msg_b), \
        # A.dpath.a_reg.line_trace(), A.dpath.b_reg.line_trace(), \
        # A.dpath.res_reg.line_trace(),\
        # "resp val:%d rdy:%d product:%d" % (A.resp_val, A.resp_rdy, A.resp_msg )
