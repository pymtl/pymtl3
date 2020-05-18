"""
======================================================================
arbiters.py
======================================================================
Collection of arbiter implementations based on vc-Arbiters.
"""

from pymtl3 import *

from .registers import RegEnRst


#-----------------------------------------------------------------------
# RoundRobinArbiter
#-----------------------------------------------------------------------
class RoundRobinArbiter( Component ):

  def construct( s, nreqs ):

    nreqsX2 = nreqs * 2
    Type    = mk_bits( nreqs )

    s.reqs   = InPort ( Type )
    s.grants = OutPort( Type )

    # priority enable

    s.priority_en = Wire()

    # priority register

    s.priority_reg = m = RegEnRst( Type, reset_value = 1 )

    connect( m.en,           s.priority_en )
    connect( m.in_[1:nreqs], s.grants[0:nreqs-1] )
    connect( m.in_[0],       s.grants[nreqs-1] )

    s.kills        = Wire( 2*nreqs + 1 )
    s.priority_int = Wire( 2*nreqs )
    s.reqs_int     = Wire( 2*nreqs )
    s.grants_int   = Wire( 2*nreqs )

    @update
    def comb_reqs_int():
      s.reqs_int [    0:nreqs  ] @= s.reqs
      s.reqs_int [nreqs:nreqsX2] @= s.reqs

    @update
    def comb_grants():
      for i in range( nreqs ):
        s.grants[i] @= s.grants_int[i] | s.grants_int[nreqs+i]

    @update
    def comb_priority_en():
      s.priority_en @= s.grants != 0

    @update
    def comb_priority_int():
      s.priority_int[    0:nreqs  ] @= s.priority_reg.out
      s.priority_int[nreqs:nreqsX2] @= 0

    @update
    def comb_kills():
      s.kills[0] @= 1
      for i in range( nreqsX2 ):
        if s.priority_int[i]:
          s.kills[i+1] @= s.reqs_int[i]
        else:
          s.kills[i+1] @= s.kills[i] | ( ~s.kills[i] & s.reqs_int[i] )

    @update
    def comb_grants_int():
      for i in range( nreqsX2 ):
        if s.priority_int[i]:
          s.grants_int[i] @= s.reqs_int[i]
        else:
          s.grants_int[i] @= ~s.kills[i] & s.reqs_int[i]

  def line_trace( s ):
    return f"{s.reqs} | {s.grants}"

#-----------------------------------------------------------------------
# RoundRobinArbiterEn
#-----------------------------------------------------------------------
class RoundRobinArbiterEn( Component ):
  '''Round Robin Arbiter model with an enable bit.

  Only when 1) the arbiter enable bit is set high AND 2) there is some
  valid arbitration, the priority register is updated. This breaks the
  val-rdy dependency.
  '''
  def construct( s, nreqs ):

    nreqsX2 = nreqs * 2
    Type    = mk_bits( nreqs )

    s.en     = InPort ()
    s.reqs   = InPort ( Type )
    s.grants = OutPort( Type )

    s.priority_en = Wire()

    s.priority_reg = m = RegEnRst( mk_bits( nreqs ), reset_value = 1 )
    m.en           //= s.priority_en
    m.in_[1:nreqs] //= s.grants[0:nreqs-1]
    m.in_[0]       //= s.grants[nreqs-1]

    s.kills        = Wire( 2*nreqs + 1 )
    s.priority_int = Wire( 2*nreqs )
    s.reqs_int     = Wire( 2*nreqs )
    s.grants_int   = Wire( 2*nreqs )

    @update
    def comb_reqs_int():
      s.reqs_int [    0:nreqs  ] @= s.reqs
      s.reqs_int [nreqs:nreqsX2] @= s.reqs

    @update
    def comb_grants():
      for i in range( nreqs ):
        s.grants[i] @= s.grants_int[i] | s.grants_int[nreqs+i]

    @update
    def comb_priority_en():
      s.priority_en @= ( s.grants != 0 ) & s.en

    @update
    def comb_priority_int():
      s.priority_int[    0:nreqs  ] @= s.priority_reg.out
      s.priority_int[nreqs:nreqsX2] @= 0

    @update
    def comb_kills():
      s.kills[0] @= 1
      for i in range( nreqsX2 ):
        if s.priority_int[i]:
          s.kills[i+1] @= s.reqs_int[i]
        else:
          s.kills[i+1] @= s.kills[i] | ( ~s.kills[i] & s.reqs_int[i] )

    @update
    def comb_grants_int():
      for i in range( nreqsX2 ):
        if s.priority_int[i]:
          s.grants_int[i] @= s.reqs_int[i]
        else:
          s.grants_int[i] @= ~s.kills[i] & s.reqs_int[i]

  def line_trace( s ):
    return f"{s.reqs} | {s.grants}"
