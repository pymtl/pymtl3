#=======================================================================
# arbiters.py
#=======================================================================
'''Collection of arbiter implementations based on vc-Arbiters.'''

from pymtl     import *
from pclib.rtl import Mux, RegEnRst

#-----------------------------------------------------------------------
# RoundRobinArbiter
#-----------------------------------------------------------------------
class RoundRobinArbiter( RTLComponent ):

  def construct( s, nreqs ):

    nreqsX2  = nreqs * 2

    s.reqs   = InVPort ( mk_bits( nreqs ) )
    s.grants = OutVPort( mk_bits( nreqs ) )

    # priority enable

    s.priority_en = Wire( Bits1 )

    # priority register

    s.priority_reg = m = RegEnRst( mk_bits( nreqs ), reset_value = 1 )

    s.connect( m.en,           s.priority_en )
    s.connect( m.in_[1:nreqs], s.grants[0:nreqs-1] )
    s.connect( m.in_[0],       s.grants[nreqs-1] )

    s.kills        = Wire( mk_bits( 2*nreqs + 1 ) )
    s.priority_int = Wire( mk_bits( 2*nreqs ) )
    s.reqs_int     = Wire( mk_bits( 2*nreqs ) )
    s.grants_int   = Wire( mk_bits( 2*nreqs ) )

    #-------------------------------------------------------------------
    # comb
    #-------------------------------------------------------------------
    @s.update
    def comb():

      s.kills[0] = 1

      s.priority_int[    0:nreqs  ] = s.priority_reg.out
      s.priority_int[nreqs:nreqsX2] = 0
      s.reqs_int    [    0:nreqs  ] = s.reqs
      s.reqs_int    [nreqs:nreqsX2] = s.reqs

      # Calculate the kill chain
      for i in range( nreqsX2 ):

        # Set internal grants
        if s.priority_int[i]:
          s.grants_int[i] = s.reqs_int[i]
        else:
          s.grants_int[i] = ~s.kills[i] & s.reqs_int[i]

        # Set kill signals
        if s.priority_int[i]:
          s.kills[i+1] = s.grants_int[i]
        else:
          s.kills[i+1] = s.kills[i] | s.grants_int[i]

      # Assign the output ports
      for i in range( nreqs ):
        s.grants[i] = s.grants_int[i] | s.grants_int[nreqs+i]

      # Set the priority enable
      s.priority_en = ( s.grants != 0 )

  def line_trace( s ):
    return "{} | {}".format( s.reqs, s.grants )

#-----------------------------------------------------------------------
# RoundRobinArbiterEn
#-----------------------------------------------------------------------
class RoundRobinArbiterEn( RTLComponent ):
  '''Round Robin Arbiter model with an enable bit.

  Only when 1) the arbiter enable bit is set high AND 2) there is some
  valid arbitration, the priority register is updated. This breaks the
  val-rdy dependency.
  '''
  def construct( s, nreqs ):

    nreqsX2  = nreqs * 2

    s.en     = InVPort ( Bits1 )
    s.reqs   = InVPort ( mk_bits( nreqs ) )
    s.grants = OutVPort( mk_bits( nreqs ) )

    # priority enable

    s.priority_en = Wire( Bits1 )

    # priority register

    s.priority_reg = m = RegEnRst( mk_bits( nreqs ), reset_value = 1 )

    s.connect( m.en,           s.priority_en )
    s.connect( m.in_[1:nreqs], s.grants[0:nreqs-1] )
    s.connect( m.in_[0],       s.grants[nreqs-1] )

    s.kills        = Wire( mk_bits( 2*nreqs + 1 ) )
    s.priority_int = Wire( mk_bits( 2*nreqs ) )
    s.reqs_int     = Wire( mk_bits( 2*nreqs ) )
    s.grants_int   = Wire( mk_bits( 2*nreqs ) )

    #-------------------------------------------------------------------
    # comb_arbitrate
    #-------------------------------------------------------------------

    @s.update
    def comb_arbitrate():

      s.kills[0] = 1

      s.priority_int[    0:nreqs  ] = s.priority_reg.out
      s.priority_int[nreqs:nreqsX2] = 0
      s.reqs_int    [    0:nreqs  ] = s.reqs
      s.reqs_int    [nreqs:nreqsX2] = s.reqs

      # Calculate the kill chain
      for i in range( nreqsX2 ):

        # Set internal grants
        if s.priority_int[i]:
          s.grants_int[i] = s.reqs_int[i]
        else:
          s.grants_int[i] = ~s.kills[i] & s.reqs_int[i]

        # Set kill signals
        if s.priority_int[i]:
          s.kills[i+1] = s.grants_int[i]
        else:
          s.kills[i+1] = s.kills[i] | s.grants_int[i]

      # Assign the output ports
      for i in range( nreqs ):
        s.grants[i] = s.grants_int[i] | s.grants_int[nreqs+i]

    #-------------------------------------------------------------------
    # comb_feedback
    #-------------------------------------------------------------------

    @s.update
    def comb_feedback():
      s.priority_en = ( s.grants != 0 ) & s.en

  def line_trace( s ):
    return "{} | {}".format( s.reqs, s.grants )
