"""
==========================================================================
MiscRTL.py
==========================================================================
Miscellaneous components for building the RTL processor.

Author : Shunning Jiang
  Date : June 13, 2019
"""
from pymtl3 import *
from pymtl3.stdlib.ifcs import GetIfcRTL, GiveIfcRTL
from pymtl3.stdlib.rtl import RegRst

from .TinyRV0InstRTL import *

# State Constants

SNOOP = b1(0)
WAIT  = b1(1)

#-------------------------------------------------------------------------
# DropUnit
#-------------------------------------------------------------------------
# Drop Unit drops a transaction between any two models connected by
# using the val-rdy handshake protocol. It receives a drop signal as an
# input and if the drop signal is high, it will drop the next message
# it sees.

class DropUnitRTL( Component ):

  def construct( s, dtype ):

    s.drop = InPort()
    s.in_  = GetIfcRTL( dtype )
    s.out  = GiveIfcRTL( dtype )

    s.out.ret //= s.in_.ret

    s.snoop_state = Wire()

    #------------------------------------------------------------------
    # state_transitions
    #------------------------------------------------------------------

    @s.update_ff
    def state_transitions():

      if s.reset:
        s.snoop_state <<= SNOOP

      elif s.snoop_state == SNOOP:
        if s.drop & ~s.in_.rdy:
          s.snoop_state <<= WAIT

      elif s.snoop_state == WAIT:
        if s.in_.rdy:
          s.snoop_state <<= SNOOP

    #------------------------------------------------------------------
    # set_outputs
    #------------------------------------------------------------------

    @s.update
    def set_outputs():
      s.out.rdy = b1(0)
      s.in_.en  = b1(0)

      if   s.snoop_state == SNOOP:
        s.out.rdy = s.in_.rdy & ~s.drop
        s.in_.en  = s.out.en

      elif s.snoop_state == WAIT:
        s.out.rdy = b1(0)
        s.in_.en  = s.in_.rdy

#-------------------------------------------------------------------------
# Generate intermediate (imm) based on type
#-------------------------------------------------------------------------

class ImmGenRTL( Component ):

  # Interface

  def construct( s ):
    dtype = mk_bits( 32 )

    s.imm_type = InPort( Bits3 )
    s.inst     = InPort( dtype )
    s.imm      = OutPort( dtype )

    @s.update
    def up_immgen():
      s.imm = dtype(0)

      # Always sext!
      if   s.imm_type == b3(0): # I-type
        s.imm = concat( sext( s.inst[ I_IMM ], 32 ) )

      elif s.imm_type == b3(2): # B-type
        s.imm = concat( sext( s.inst[ B_IMM3 ], 20 ),
                                    s.inst[ B_IMM2 ],
                                    s.inst[ B_IMM1 ],
                                    s.inst[ B_IMM0 ],
                                    Bits1( 0 ) )

      elif s.imm_type == b3(1): # S-type
        s.imm = concat( sext( s.inst[ S_IMM1 ], 27 ),
                              s.inst[ S_IMM0 ] )

#-------------------------------------------------------------------------
# ALU
#-------------------------------------------------------------------------

class AluRTL( Component ):

  def construct( s, nbits=32 ):
    dtype = mk_bits( nbits )

    s.in0      = InPort ( dtype )
    s.in1      = InPort ( dtype )
    s.fn       = InPort ( Bits4 )

    s.out      = OutPort( dtype )
    s.ops_ne   = OutPort( Bits1 )

    @s.update
    def comb_logic():
      if   s.fn == b4(0): s.out = s.in0               # COPY OP0
      elif s.fn == b4(1): s.out = s.in1               # COPY OP1
      elif s.fn == b4(2): s.out = s.in0 + s.in1       # ADD
      elif s.fn == b4(3): s.out = s.in0 << s.in1[0:5] # SLL
      elif s.fn == b4(4): s.out = s.in0 >> s.in1[0:5] # SRL

      # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''
      # Implement AND in the ALU
      # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
      #; Add code to implement a bitwise-and operation for in0 and in1.

      elif s.fn == b4(5): s.out = s.in0 & s.in1       # AND

      # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

      else:               s.out = dtype(0)            # Unknown

      s.ops_ne = s.in0 != s.in1

  def line_trace( s ):
    op_dict = { 0:" +", 1:"c0", 2:"c1", 3:"<< ", 4:" &"}
    return "[{}({} ){} >>> {}]".format( s.in0, op_dict[int(s.fn)], s.in1, s.out )
