#=========================================================================
# lfsr.py
#=========================================================================
# Author: Shunning Jiang
# Date  : Dec 19, 2019

"""
RTL implementation of Linear-feedback shift register (LFSR)
"""

from pymtl3 import *

LFSR_table = {
  32: (31,29,26,25),
  60: (59,58),
  64: (63,62,60,59),
}

class LFSR( Component ):
  """ bsg_lfsr

  https://github.com/bespoke-silicon-group/basejump_stl/blob/master/bsg_misc/bsg_lfsr.v

  Args:
    width (int): bitwidth of the shift register
    init_value (int): the reset value of the register
    xor_mask (int): the XOR mask of the LFSR. Note that XOR mask starts at
                    bit 0; which may be shifted from mathematician's notation.

  Variables:
    yumi_i: Input yumi signal that enables shifting in the cycle
    o: LFSR output value
  """

  def construct( s, width, init_value=1, xor_mask=0 ):

    # Process parameters

    assert width > 0
    DType = mk_bits(width)

    if xor_mask == 0:
      assert width in LFSR_table, f"FIXME: {width}-bit xor_mask is not given and not available in LFSR_table"
      for k in LFSR_table[ width ]:
        xor_mask |= 1 << k

    xor_mask = DType( xor_mask )

    # Interfaces

    s.yumi_i = InPort()
    s.o      = OutPort( DType )

    s.o_r = Wire( DType )
    s.o_r //= s.o

    @s.update_ff
    def seq_lfsr():

      if s.reset:
        s.o_r <<= DType( init_value )

      elif s.yumi_i:
        s.o_r <<= (s.o_r >> 1) ^ DType( sext( s.o_r[0], width ) & xor_mask )

  def line_trace( s ):
    return f"[{s.o_r}]"

x = LFSR(32)
x.elaborate()
x.apply( SimulationPass() )

x.sim_reset()

for i in range(10):
  x.yumi_i = b1(1)
  x.eval_combinational()
  print(x.o)
  x.tick()
