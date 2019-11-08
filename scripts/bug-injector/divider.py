from pymtl3.passes import SimulationPass
from pymtl3.dsl import Component, InPort, OutPort, Wire, Const, connect
from pymtl3.datatypes import Bits1, Bits2, Bits4, Bits5, Bits8, Bits16, Bits32, get_nbits
from pymtl3.stdlib.rtl import RegEn, Reg, Mux, RShifter, LShifter, Subtractor
from pymtl3.stdlib.ifcs   import InValRdyIfc, OutValRdyIfc

from typing import TypeVar, Generic

Q_MUX_SEL_0   = 0
Q_MUX_SEL_LSH = 1

R_MUX_SEL_IN    = 0
R_MUX_SEL_SUB1  = 1
R_MUX_SEL_SUB2  = 2

D_MUX_SEL_IN  = 0
D_MUX_SEL_RSH = 1

T_IDivDpath = TypeVar( 'T_IDivDpath' )
T_IDivDpathx2 = TypeVar( 'T_IDivDpathx2' )

class IntDivRem4Dpath( Component, Generic[T_IDivDpath, T_IDivDpathx2] ):

  def construct( s ) -> None:

    nbits = get_nbits( T_IDivDpath )
    nbitsx2 = nbits*2

    s.req_msg  = InPort[T_IDivDpathx2]()
    s.resp_msg = OutPort[T_IDivDpathx2]()

    # Status signals

    s.sub_negative1 = OutPort[Bits1]()
    s.sub_negative2 = OutPort[Bits1]()

    # Control signals

    s.quotient_mux_sel  = InPort[Bits1]()
    s.quotient_reg_en   = InPort[Bits1]()

    s.remainder_mux_sel = InPort[Bits2]()
    s.remainder_reg_en  = InPort[Bits1]()

    s.divisor_mux_sel   = InPort[Bits1]()

    # Dpath components

    s.remainder_mux = Mux[T_IDivDpathx2, Bits2]( 3 )
    connect( s.remainder_mux.sel, s.remainder_mux_sel )

    @s.update
    def up_remainder_mux_in0() -> None:
      s.remainder_mux.in_[R_MUX_SEL_IN] = Const[T_IDivDpathx2](0)
      s.remainder_mux.in_[R_MUX_SEL_IN][0:nbits] = s.req_msg[0:nbits]

    s.remainder_reg = RegEn[T_IDivDpathx2]()
    connect( s.remainder_reg.in_, s.remainder_mux.out )
    connect( s.remainder_reg.en,  s.remainder_reg_en  )

    # lower bits of resp_msg save the remainder
    connect( s.resp_msg[0:nbits], s.remainder_reg.out[0:nbits] )

    s.divisor_mux = Mux[T_IDivDpathx2, Bits1]( 2 )
    connect( s.divisor_mux.sel, s.divisor_mux_sel )

    @s.update
    def up_divisor_mux_in0() -> None:
      s.divisor_mux.in_[D_MUX_SEL_IN] = Const[T_IDivDpathx2]()
      s.divisor_mux.in_[D_MUX_SEL_IN][nbits-1:nbitsx2-1] = s.req_msg[nbits:nbitsx2]

    s.divisor_reg   = Reg[T_IDivDpathx2]()
    connect( s.divisor_reg.in_, s.divisor_mux.out )

    s.quotient_mux  = Mux[T_IDivDpath, Bits1]( 2 )
    connect( s.quotient_mux.sel, s.quotient_mux_sel )
    connect( s.quotient_mux.in_[Q_MUX_SEL_0], Const[T_IDivDpath](0) )

    s.quotient_reg  = RegEn[T_IDivDpath]()
    connect( s.quotient_reg.in_, s.quotient_mux.out )
    connect( s.quotient_reg.en,  s.quotient_reg_en  )
    connect( s.quotient_reg.out, s.resp_msg[nbits:nbitsx2] )

    # shamt should be 2 bits!
    s.quotient_lsh = LShifter[T_IDivDpath, Bits2]()
    connect( s.quotient_lsh.in_, s.quotient_reg.out )
    connect( s.quotient_lsh.shamt, Const[Bits2](2) )

    s.inc = Wire[Bits2]()
    connect( s.sub_negative1, s.inc[1] )
    connect( s.sub_negative2, s.inc[0] )

    @s.update
    def up_quotient_inc() -> None:
      s.quotient_mux.in_[Q_MUX_SEL_LSH] = s.quotient_lsh.out + Const[T_IDivDpath](~s.inc)

    # stage 1/2

    s.sub1 = Subtractor[T_IDivDpathx2]()
    connect( s.sub1.in0, s.remainder_reg.out )
    connect( s.sub1.in1, s.divisor_reg.out   )
    connect( s.sub1.out, s.remainder_mux.in_[R_MUX_SEL_SUB1] )
    connect( s.sub_negative1, s.sub1.out[nbitsx2-1] )

    s.remainder_mid_mux = Mux[T_IDivDpathx2, Bits1]( 2 )
    connect( s.remainder_mid_mux.in_[0], s.sub1.out          )
    connect( s.remainder_mid_mux.in_[1], s.remainder_reg.out )
    connect( s.remainder_mid_mux.sel,    s.sub_negative1     )

    s.divisor_rsh1 = RShifter[T_IDivDpathx2, Bits1]()
    connect( s.divisor_rsh1.in_, s.divisor_reg.out )
    connect( s.divisor_rsh1.shamt, Const[Bits1](1) )

    # stage 2/2

    s.sub2 = Subtractor[T_IDivDpathx2]()
    connect( s.sub2.in0, s.remainder_mid_mux.out             )
    connect( s.sub2.in1, s.divisor_rsh1.out                  )
    connect( s.sub2.out, s.remainder_mux.in_[R_MUX_SEL_SUB2] )

    connect( s.sub_negative2, s.sub2.out[nbitsx2-1] )

    s.divisor_rsh2 = RShifter[T_IDivDpathx2, Bits1]()
    connect( s.divisor_rsh2.in_, s.divisor_rsh1.out               )
    connect( s.divisor_rsh2.out, s.divisor_mux.in_[D_MUX_SEL_RSH] )
    connect( s.divisor_rsh2.shamt, Const[Bits1](1)                )

T_IDivCtrl = TypeVar( 'T_IDivCtrl' )
T_IDivCtrlState = TypeVar( 'T_IDivCtrlState' )

class IntDivRem4Ctrl( Component, Generic[T_IDivCtrl, T_IDivCtrlState] ):

  def construct( s ):
    nbits = get_nbits( T_IDivCtrl )

    s.req_val  = InPort [Bits1]()
    s.req_rdy  = OutPort[Bits1]()
    s.resp_val = OutPort[Bits1]()
    s.resp_rdy = InPort [Bits1]()

    # Status signals

    s.sub_negative1 = InPort[Bits1]()
    s.sub_negative2 = InPort[Bits1]()

    # Control signals

    s.quotient_mux_sel  = OutPort[Bits1]()
    s.quotient_reg_en   = OutPort[Bits1]()

    s.remainder_mux_sel = OutPort[Bits2]()
    s.remainder_reg_en  = OutPort[Bits1]()

    s.divisor_mux_sel   = OutPort[Bits1]()

    s.state = Reg[T_IDivCtrlState]()

    s.STATE_IDLE = Const[T_IDivCtrlState](0)
    s.STATE_DONE = Const[T_IDivCtrlState](1)
    s.STATE_CALC = Const[T_IDivCtrlState](1+nbits//2)

    @s.update
    def state_transitions() -> None:

      curr_state = s.state.out

      if   curr_state == s.STATE_IDLE:
        if s.req_val and s.req_rdy:
          s.state.in_ = s.STATE_CALC

      elif curr_state == s.STATE_DONE:
        if s.resp_val and s.resp_rdy:
          s.state.in_ = s.STATE_IDLE

      else:
        s.state.in_ = curr_state - Const[T_IDivCtrlState](1)

    @s.update
    def state_outputs() -> None:

      curr_state = s.state.out

      if   curr_state == s.STATE_IDLE:
        s.req_rdy     = Const[Bits1]( 1 )
        s.resp_val    = Const[Bits1]( 0 )

        s.remainder_mux_sel = Const[Bits2]( R_MUX_SEL_IN )
        s.remainder_reg_en  = Const[Bits1]( 1 )

        s.quotient_mux_sel  = Const[Bits1]( Q_MUX_SEL_0 )
        s.quotient_reg_en   = Const[Bits1]( 1 )

        s.divisor_mux_sel   = Const[Bits1]( D_MUX_SEL_IN )

      elif curr_state == s.STATE_DONE:
        s.req_rdy     = Const[Bits1]( 0 )
        s.resp_val    = Const[Bits1]( 1 )

        s.quotient_mux_sel  = Const[Bits1]( Q_MUX_SEL_0 )
        s.quotient_reg_en   = Const[Bits1]( 0 )

        s.remainder_mux_sel = Const[Bits2]( R_MUX_SEL_IN )
        s.remainder_reg_en  = Const[Bits1]( 0 )

        s.divisor_mux_sel   = Const[Bits1]( D_MUX_SEL_IN )

      else: # calculating
        s.req_rdy     = Const[Bits1]( 0 )
        s.resp_val    = Const[Bits1]( 0 )

        s.remainder_reg_en = ~(s.sub_negative1 & s.sub_negative2)
        if s.sub_negative2:
          s.remainder_mux_sel = Const[Bits2]( R_MUX_SEL_SUB1 )
        else:
          s.remainder_mux_sel = Const[Bits2]( R_MUX_SEL_SUB2 )

        s.quotient_reg_en   = Const[Bits1]( 1 )
        s.quotient_mux_sel  = Const[Bits1]( Q_MUX_SEL_LSH )

        s.divisor_mux_sel   = Const[Bits1]( D_MUX_SEL_RSH )

# nbits
T_IDiv = TypeVar( 'T_IDiv' )
# nbits*2
T_IDiv2 = TypeVar( 'T_IDiv2' )
# 1+clog2(nbits)
T_IDivState = TypeVar( 'T_IDivState' )

class IntDivRem4( Component, Generic[T_IDiv, T_IDiv2, T_IDivState] ):

  def construct( s ) -> None:
    nbits = get_nbits( T_IDiv )
    assert nbits % 2 == 0

    s.req  = InValRdyIfc [T_IDiv2]()
    s.resp = OutValRdyIfc[T_IDiv2]()

    s.dpath = IntDivRem4Dpath[T_IDiv, T_IDiv2]()
    connect( s.dpath.req_msg,  s.req.msg  )
    connect( s.dpath.resp_msg, s.resp.msg )

    s.ctrl = IntDivRem4Ctrl[T_IDiv, T_IDivState]()
    connect( s.ctrl.req_val,  s.req.val  )
    connect( s.ctrl.req_rdy,  s.req.rdy  )
    connect( s.ctrl.resp_val, s.resp.val )
    connect( s.ctrl.resp_rdy, s.resp.rdy )

    connect( s.ctrl.sub_negative1, s.dpath.sub_negative1 )
    connect( s.ctrl.sub_negative2, s.dpath.sub_negative2 )

    connect( s.ctrl.quotient_mux_sel, s.dpath.quotient_mux_sel )
    connect( s.ctrl.quotient_reg_en,  s.dpath.quotient_reg_en  )

    connect( s.ctrl.remainder_mux_sel, s.dpath.remainder_mux_sel )
    connect( s.ctrl.remainder_reg_en,  s.dpath.remainder_reg_en  )

    connect( s.ctrl.divisor_mux_sel, s.dpath.divisor_mux_sel )

  def line_trace( s ) -> str:
    dpath, ctrl = s.dpath, s.ctrl
    return "Rem:{} Quo:{} Div:{}".format( s.dpath.remainder_reg.out,
                                          s.dpath.quotient_reg.out,
                                          s.dpath.divisor_reg.out )
