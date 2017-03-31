from pymtl import *
from pclib.update import RegEn, Reg, Mux, RShifter, LShifter, Adder, ZeroComp
from pclib.bundle import ValRdyBundle

class StepIfc( PortBundle ):
  def __init__( s ):
    s.val  = ValuePort( Bits1  )
    s.a    = ValuePort( Bits32 )
    s.b    = ValuePort( Bits32 )
    s.res  = ValuePort( Bits32 )

class IntMulNstageStep( Updates ):

  def __init__( s ):
    s.in_ = StepIfc()
    s.out = StepIfc()

    s.out.val |= s.in_.val

    s.a_lsh       = LShifter( Bits32 )
    s.a_lsh.in_  |= s.in_.a
    s.a_lsh.out  |= s.out.a
    s.a_lsh.shamt = Bits1( 1 )

    s.b_rsh       = RShifter( Bits32 )
    s.b_rsh.in_  |= s.in_.b
    s.b_rsh.out  |= s.out.b
    s.b_rsh.shamt = Bits1( 1 )

    s.adder = Adder( Bits32 )
    s.adder.in0  |= s.in_.a
    s.adder.in1  |= s.in_.res

    s.mux   = Mux( Bits32, 1 )
    s.mux.in_[0] |= s.in_.res
    s.mux.in_[1] |= s.adder.out
    s.mux.sel    |= s.in_.b[0]
    s.mux.out    |= s.out.res

  def line_trace( s ):
    return str(s.out.res)

class IntMulNstageInelastic( Updates ):

  def __init__( s, nstages = 4 ):

    s.req  = ValRdyBundle( Bits64 )
    s.resp = ValRdyBundle( Bits32 )

    assert nstages in [1,2,4,8,16,32]
    steps_per_stage = 32/nstages

    # Pipeline registers, I merge input registers into the same array

    s.a_preg   = [ RegEn(Bits32) for _ in xrange(nstages) ]
    s.b_preg   = [ RegEn(Bits32) for _ in xrange(nstages) ]
    s.val_preg = [ RegEn(Bits1 ) for _ in xrange(nstages) ]
    s.res_preg = [ RegEn(Bits32) for _ in xrange(nstages) ]

    s.steps = [ IntMulNstageStep() for _ in xrange(32) ]

    # The 0-th step

    s.  a_preg[0].in_ |= s.req.msg[0:32]
    s.  b_preg[0].in_ |= s.req.msg[32:64]
    s.val_preg[0].in_ |= s.req.val
    s.res_preg[0].in_  = Bits1( 0 )
    s.  a_preg[0].en  |= s.resp.rdy
    s.  b_preg[0].en  |= s.resp.rdy
    s.val_preg[0].en  |= s.resp.rdy
    s.res_preg[0].en  |= s.resp.rdy

    s.steps[0].in_.a   |= s.  a_preg[0].out
    s.steps[0].in_.b   |= s.  b_preg[0].out
    s.steps[0].in_.val |= s.val_preg[0].out
    s.steps[0].in_.res |= s.res_preg[0].out

    for i in xrange(1,32):

      if i % steps_per_stage == 0:
        stage = i / steps_per_stage

        # Insert a pipeline register

        s.  a_preg[stage].in_ |= s.steps[i-1].out.a
        s.  b_preg[stage].in_ |= s.steps[i-1].out.b
        s.val_preg[stage].in_ |= s.steps[i-1].out.val
        s.res_preg[stage].in_ |= s.steps[i-1].out.res
        s.  a_preg[stage].en  |= s.resp.rdy
        s.  b_preg[stage].en  |= s.resp.rdy
        s.val_preg[stage].en  |= s.resp.rdy
        s.res_preg[stage].en  |= s.resp.rdy

        s.steps[i].in_.a   |= s.  a_preg[stage].out
        s.steps[i].in_.b   |= s.  b_preg[stage].out
        s.steps[i].in_.val |= s.val_preg[stage].out
        s.steps[i].in_.res |= s.res_preg[stage].out

      else:
        s.steps[i].in_ |= s.steps[i-1].out

    # The last step

    s.resp.val |= s.steps[31].out.val
    s.resp.msg |= s.steps[31].out.res

    # Wire resp rdy to req rdy

    s.req.rdy  |= s.resp.rdy

  def line_trace( s ):
    return "{}".format(
      ' '.join([ x.line_trace() for x in s.val_preg])
    )
