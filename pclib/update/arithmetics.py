from pymtl import *

# N-input Mux

class Mux(Updates):

  def __init__( s, type_, sel_nbits ):
    s.in_ = [ ValuePort( type_ ) for _ in xrange(1<<sel_nbits) ]
    s.sel = ValuePort( mk_bits( sel_nbits ) )
    s.out = ValuePort( type_ )

    @s.update
    def up_mux():
      s.out = s.in_[ s.sel ]

  def line_trace( s ):  pass

# Rshifter

class RShifter(Updates):

  def __init__( s, type_, shamt_nbits = 1 ):
    s.in_   = ValuePort( type_ )
    s.shamt = ValuePort( mk_bits( shamt_nbits ) )
    s.out   = ValuePort( type_ )

    @s.update
    def up_rshifter():
      s.out = s.in_ >> s.shamt

  def line_trace( s ):  pass

# Lshifter

class LShifter(Updates):

  def __init__( s, type_, shamt_nbits = 1 ):
    s.in_   = ValuePort( type_ )
    s.shamt = ValuePort( mk_bits( shamt_nbits ) )
    s.out   = ValuePort( type_ ) 

    @s.update
    def up_lshifter():
      s.out = s.in_ << s.shamt

  def line_trace( s ):  pass

# Adder 

class Adder(Updates):

  def __init__( s, type_ ):
    s.in0 = ValuePort( type_ )
    s.in1 = ValuePort( type_ )
    s.out = ValuePort( type_ )

    @s.update
    def up_adder():
      s.out = s.in0 + s.in1

  def line_trace( s ):  pass

# Subtractor

class Subtractor(Updates):

  def __init__( s, type_ ):
    s.in0 = ValuePort( type_ )
    s.in1 = ValuePort( type_ )
    s.out = ValuePort( type_ )

    @s.update
    def up_subtractor():
      s.out = s.in0 - s.in1

  def line_trace( s ):  pass

# ZeroComparator 

class ZeroComp(Updates):

  def __init__( s, type_ ):
    s.in_ = ValuePort( type_ )
    s.out = ValuePort( Bits1 )

    @s.update
    def up_zerocomp():
      s.out = Bits1( s.in_ == 0 )

  def line_trace( s ):  pass

# LeftThanComparator

class LTComp(Updates):

  def __init__( s, type_ ):
    s.in0 = ValuePort( type_ )
    s.in1 = ValuePort( type_ )
    s.out = ValuePort( Bits1 )

    @s.update
    def up_ltcomp():
      s.out = Bits1(s.in0 < s.in1)

  def line_trace( s ):  pass

# LeftThanOrEqualToComparator

class LEComp(Updates):

  def __init__( s, type_ ):
    s.in0 = ValuePort( type_ )
    s.in1 = ValuePort( type_ )
    s.out = ValuePort( Bits1 )

    @s.update
    def up_lecomp():
      s.out = Bits1(s.in0 <= s.in1)

  def line_trace( s ):  pass
