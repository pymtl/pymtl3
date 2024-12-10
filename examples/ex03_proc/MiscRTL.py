"""
==========================================================================
MiscRTL.py
==========================================================================
Miscellaneous components for building the RTL processor.

Author : Shunning Jiang
  Date : June 13, 2019
"""
from pymtl3 import *
from pymtl3.stdlib.stream.ifcs import IStreamIfc, OStreamIfc
from pymtl3.stdlib.primitive import RegRst

from .TinyRV0InstRTL import *

# State Constants

SNOOP = 0
WAIT  = 1

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
    s.in_  = IStreamIfc( dtype )
    s.out  = OStreamIfc( dtype )

    s.out.msg //= s.in_.msg

    s.snoop_state = Wire()

    #------------------------------------------------------------------
    # state_transitions
    #------------------------------------------------------------------

    @update_ff
    def state_transitions():

      if s.reset:
        s.snoop_state <<= SNOOP

      elif s.snoop_state == SNOOP:
        if s.drop & ~s.in_.val:
          s.snoop_state <<= WAIT

      elif s.snoop_state == WAIT:
        if s.in_.val:
          s.snoop_state <<= SNOOP

    #------------------------------------------------------------------
    # set_outputs
    #------------------------------------------------------------------

    @update
    def set_outputs():
      s.out.val @= 0
      s.in_.rdy @= 0

      if   s.snoop_state == SNOOP:
        s.out.val @= s.in_.val & ~s.drop
        s.in_.rdy @= s.out.rdy

      elif s.snoop_state == WAIT:
        s.out.val @= 0
        s.in_.rdy @= s.in_.val

#-------------------------------------------------------------------------
# Generate intermediate (imm) based on type
#-------------------------------------------------------------------------

class ImmGenRTL( Component ):

  # Interface

  def construct( s ):

    s.imm_type = InPort( 3 )
    s.inst     = InPort( 32 )
    s.imm      = OutPort( 32 )

    @update
    def up_immgen():
      s.imm @= 0

      # Always sext!
      if   s.imm_type == 0: # I-type
        s.imm @= concat( sext( s.inst[ I_IMM ], 32 ) )

      elif s.imm_type == 2: # B-type
        s.imm @= concat( sext( s.inst[ B_IMM3 ], 20 ),
                               s.inst[ B_IMM2 ],
                               s.inst[ B_IMM1 ],
                               s.inst[ B_IMM0 ],
                               b1( 0 ) )

      elif s.imm_type == 1: # S-type
        s.imm @= concat( sext( s.inst[ S_IMM1 ], 27 ),
                               s.inst[ S_IMM0 ] )

#-------------------------------------------------------------------------
# ALU
#-------------------------------------------------------------------------

class AluRTL( Component ):

  def construct( s, nbits=32 ):

    s.in0      = InPort ( nbits )
    s.in1      = InPort ( nbits )
    s.fn       = InPort ( 4 )

    s.out      = OutPort( nbits )
    s.ops_ne   = OutPort()

    @update
    def comb_logic():
      if   s.fn == 0: s.out @= s.in0               # COPY OP0
      elif s.fn == 1: s.out @= s.in1               # COPY OP1
      elif s.fn == 2: s.out @= s.in0 + s.in1       # ADD
      elif s.fn == 3: s.out @= s.in0 << zext(s.in1[0:5], 32) # SLL
      elif s.fn == 4: s.out @= s.in0 >> zext(s.in1[0:5], 32) # SRL

      # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''
      # Implement AND in the ALU
      # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
      #; Add code to implement a bitwise-and operation for in0 and in1.

      elif s.fn == 5: s.out @= s.in0 & s.in1       # AND

      # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

      else:           s.out @= 0            # Unknown

      s.ops_ne @= s.in0 != s.in1

  def line_trace( s ):
    op_dict = { 0:" +", 1:"c0", 2:"c1", 3:"<< ", 4:" &"}
    return "[{}({} ){} >>> {}]".format( s.in0, op_dict[int(s.fn)], s.in1, s.out )
