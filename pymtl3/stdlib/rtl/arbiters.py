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

    s.priority_en = Wire( Bits1 )

    # priority register

    s.priority_reg = m = RegEnRst( Type, reset_value = 1 )

    connect( m.en,           s.priority_en )
    connect( m.in_[1:nreqs], s.grants[0:nreqs-1] )
    connect( m.in_[0],       s.grants[nreqs-1] )

    s.kills        = Wire( mk_bits( 2*nreqs + 1 ) )
    s.priority_int = Wire( mk_bits( 2*nreqs ) )
    s.reqs_int     = Wire( mk_bits( 2*nreqs ) )
    s.grants_int   = Wire( mk_bits( 2*nreqs ) )

    #-------------------------------------------------------------------
    # comb_reqs_int
    #-------------------------------------------------------------------

    @s.update
    def comb_reqs_int():

      s.reqs_int [    0:nreqs  ] = s.reqs
      s.reqs_int [nreqs:nreqsX2] = s.reqs

    #-------------------------------------------------------------------
    # comb_grants
    #-------------------------------------------------------------------

    @s.update
    def comb_grants():

      # Assign the output ports
      for i in range( nreqs ):
        s.grants[i] = s.grants_int[i] | s.grants_int[nreqs+i]

    #-------------------------------------------------------------------
    # comb_priority_en
    #-------------------------------------------------------------------

    @s.update
    def comb_priority_en():

      # Set the priority enable
      s.priority_en = ( s.grants != Type(0) )

    #-------------------------------------------------------------------
    # comb_priority_int
    #-------------------------------------------------------------------

    @s.update
    def comb_priority_int():

      s.priority_int[    0:nreqs  ] = s.priority_reg.out
      s.priority_int[nreqs:nreqsX2] = Type(0)

    #-------------------------------------------------------------------
    # comb_kills
    #-------------------------------------------------------------------

    @s.update
    def comb_kills():

      # Set kill signals

      s.kills[0] = Bits1(1)

      for i in range( nreqsX2 ):

        if s.priority_int[i]:
          s.kills[i+1] = s.reqs_int[i]

        else:
          s.kills[i+1] = s.kills[i] | ( ~s.kills[i] & s.reqs_int[i] )

    #-------------------------------------------------------------------
    # comb_grants_int
    #-------------------------------------------------------------------

    @s.update
    def comb_grants_int():

      for i in range( nreqsX2 ):

        # Set internal grants

        if s.priority_int[i]:
          s.grants_int[i] = s.reqs_int[i]

        else:
          s.grants_int[i] = ~s.kills[i] & s.reqs_int[i]

  def line_trace( s ):
    return "{} | {}".format( s.reqs, s.grants )

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

    s.en     = InPort ( Bits1 )
    s.reqs   = InPort ( Type )
    s.grants = OutPort( Type )

    # priority enable

    s.priority_en = Wire( Bits1 )

    # priority register

    s.priority_reg = m = RegEnRst( mk_bits( nreqs ), reset_value = 1 )

    connect( m.en,           s.priority_en )
    connect( m.in_[1:nreqs], s.grants[0:nreqs-1] )
    connect( m.in_[0],       s.grants[nreqs-1] )

    s.kills        = Wire( mk_bits( 2*nreqs + 1 ) )
    s.priority_int = Wire( mk_bits( 2*nreqs ) )
    s.reqs_int     = Wire( mk_bits( 2*nreqs ) )
    s.grants_int   = Wire( mk_bits( 2*nreqs ) )

    #-------------------------------------------------------------------
    # comb_reqs_int
    #-------------------------------------------------------------------

    @s.update
    def comb_reqs_int():

      s.reqs_int [    0:nreqs  ] = s.reqs
      s.reqs_int [nreqs:nreqsX2] = s.reqs

    #-------------------------------------------------------------------
    # comb_grants
    #-------------------------------------------------------------------

    @s.update
    def comb_grants():

      # Assign the output ports
      for i in range( nreqs ):
        s.grants[i] = s.grants_int[i] | s.grants_int[nreqs+i]

    #-------------------------------------------------------------------
    # comb_priority_en
    #-------------------------------------------------------------------

    @s.update
    def comb_priority_en():

      # Set the priority enable
      s.priority_en = ( s.grants != Type(0) ) & s.en

    #-------------------------------------------------------------------
    # comb_priority_int
    #-------------------------------------------------------------------

    @s.update
    def comb_priority_int():

      s.priority_int[    0:nreqs  ] = s.priority_reg.out
      s.priority_int[nreqs:nreqsX2] = Type(0)

    #-------------------------------------------------------------------
    # comb_kills
    #-------------------------------------------------------------------

    @s.update
    def comb_kills():

      # Set kill signals

      s.kills[0] = Bits1(1)

      for i in range( nreqsX2 ):

        if s.priority_int[i]:
          s.kills[i+1] = s.reqs_int[i]

        else:
          s.kills[i+1] = s.kills[i] | ( ~s.kills[i] & s.reqs_int[i] )

    #-------------------------------------------------------------------
    # comb_grants_int
    #-------------------------------------------------------------------

    @s.update
    def comb_grants_int():

      for i in range( nreqsX2 ):

        # Set internal grants

        if s.priority_int[i]:
          s.grants_int[i] = s.reqs_int[i]

        else:
          s.grants_int[i] = ~s.kills[i] & s.reqs_int[i]

  def line_trace( s ):
    return "{} | {}".format( s.reqs, s.grants )
