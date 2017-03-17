from pymtl import *
from pclib.update import RegEn, Reg, Mux, RShifter, LShifter, Adder, ZeroComp
from pclib.update import TestSourceValRdy, TestSinkValRdy
from pclib.valrdy import valrdy_to_str

class IntMulNstageStep( Updates ):

  def __init__( s ):
    s.in_val  = ValuePort(int)
    s.in_a    = ValuePort(int)
    s.in_b    = ValuePort(int)
    s.in_res  = ValuePort(int)

    s.out_val = ValuePort(int)
    s.out_a   = ValuePort(int)
    s.out_b   = ValuePort(int)
    s.out_res = ValuePort(int)

    s.out_val |= s.in_val

    s.a_lsh = LShifter( 32 )
    s.a_lsh.in_  |= s.in_a
    s.out_a      |= s.a_lsh.out
    s.a_lsh.shamt = 1

    s.b_rsh = RShifter( 32 )
    s.b_rsh.in_  |= s.in_b
    s.out_b      |= s.b_rsh.out
    s.b_rsh.shamt = 1

    s.adder = Adder( 32 )
    s.adder.in_[0] |= s.in_a
    s.adder.in_[1] |= s.in_res

    s.mux   = Mux( 2 )
    s.out_res    |= s.mux.out
    s.mux.in_[0] |= s.in_res
    s.mux.in_[1] |= s.adder.out

    @s.update
    def up_muxsel():
      s.mux.sel = s.in_b & 1

  def line_trace( s ):
    return str(s.out_res)

class IntMulNstageInelastic( Updates ):

  def __init__( s, nstages = 2 ):

    s.req_rdy   = ValuePort(int)
    s.req_val   = ValuePort(int)
    s.req_msg_a = ValuePort(int)
    s.req_msg_b = ValuePort(int)
    s.resp_rdy  = ValuePort(int)
    s.resp_val  = ValuePort(int)
    s.resp_msg  = ValuePort(int)

    assert nstages in [1,2,4,8,16,32]
    steps_per_stage = 32/nstages

    # Pipeline registers, I merge input registers into the same array

    s.a_preg   = [ RegEn(32) for _ in xrange(nstages) ]
    s.b_preg   = [ RegEn(32) for _ in xrange(nstages) ]
    s.val_preg = [ RegEn(1)  for _ in xrange(nstages) ]
    s.res_preg = [ RegEn(32) for _ in xrange(nstages) ]

    s.steps = [ IntMulNstageStep() for _ in xrange(32) ]

    # The 0-th step

    s.  a_preg[0].in_ |= s.req_msg_a
    s.  b_preg[0].in_ |= s.req_msg_b
    s.val_preg[0].in_ |= s.req_val
    s.res_preg[0].in_  = 0
    s.  a_preg[0].en  |= s.resp_rdy
    s.  b_preg[0].en  |= s.resp_rdy
    s.val_preg[0].en  |= s.resp_rdy
    s.res_preg[0].en  |= s.resp_rdy

    s.steps[0].in_a   |= s.  a_preg[0].out
    s.steps[0].in_b   |= s.  b_preg[0].out
    s.steps[0].in_val |= s.val_preg[0].out
    s.steps[0].in_res |= s.res_preg[0].out

    for i in xrange(1,32):

      if i % steps_per_stage == 0:
        stage = i / steps_per_stage

        # Insert a pipeline register

        s.  a_preg[stage].in_ |= s.steps[i-1].out_a
        s.  b_preg[stage].in_ |= s.steps[i-1].out_b
        s.val_preg[stage].in_ |= s.steps[i-1].out_val
        s.res_preg[stage].in_ |= s.steps[i-1].out_res
        s.  a_preg[stage].en  |= s.resp_rdy
        s.  b_preg[stage].en  |= s.resp_rdy
        s.val_preg[stage].en  |= s.resp_rdy
        s.res_preg[stage].en  |= s.resp_rdy

        s.steps[i].in_a   |= s.  a_preg[stage].out
        s.steps[i].in_b   |= s.  b_preg[stage].out
        s.steps[i].in_val |= s.val_preg[stage].out
        s.steps[i].in_res |= s.res_preg[stage].out

      else:
        s.steps[i].in_a   |= s.steps[i-1].out_a
        s.steps[i].in_b   |= s.steps[i-1].out_b
        s.steps[i].in_val |= s.steps[i-1].out_val
        s.steps[i].in_res |= s.steps[i-1].out_res

    # The last step

    s.resp_val |= s.steps[31].out_val
    s.resp_msg |= s.steps[31].out_res

    # Wire resp rdy to req rdy

    s.req_rdy  |= s.resp_rdy

  def line_trace( s ):
    return "{}".format(
      ' '.join([ x.line_trace() for x in s.val_preg])
    )

class TestHarness( Updates ):

  def __init__( s ):

    s.src  = TestSourceValRdy( 2, [ (60,35), (18,24), (195,43) ])
    s.imul = IntMulNstageInelastic()
    s.sink = TestSinkValRdy( [ 2100, 432, 8385 ] )

    s.src.val    |= s.imul.req_val
    s.src.rdy    |= s.imul.req_rdy
    s.src.msg[0] |= s.imul.req_msg_a
    s.src.msg[1] |= s.imul.req_msg_b

    s.sink.val   |= s.imul.resp_val
    s.sink.rdy   |= s.imul.resp_rdy
    s.sink.msg   |= s.imul.resp_msg

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.imul.line_trace()+" >>> "+s.sink.line_trace()

if __name__ == "__main__":
  A = TestHarness()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()
