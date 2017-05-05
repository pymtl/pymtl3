from pymtl import *

# N-input Mux

class Mux( UpdatesImpl ):

  def __init__( s, Type, sel_nbits ):
    s.in_ = [ ValuePort( Type ) for _ in xrange(1<<sel_nbits) ]
    s.sel = ValuePort( mk_bits( sel_nbits ) )
    s.out = ValuePort( Type )

    @s.update
    def up_mux():
      s.out = s.in_[ s.sel ]

  def line_trace( s ):  pass

# Rshifter

class RShifter( UpdatesImpl ):

  def __init__( s, Type, shamt_nbits = 1 ):
    s.in_   = ValuePort( Type )
    s.shamt = ValuePort( mk_bits( shamt_nbits ) )
    s.out   = ValuePort( Type )

    @s.update
    def up_rshifter():
      s.out = s.in_ >> s.shamt

  def line_trace( s ):  pass

# Lshifter

class LShifter( UpdatesImpl ):

  def __init__( s, Type, shamt_nbits = 1 ):
    s.in_   = ValuePort( Type )
    s.shamt = ValuePort( mk_bits( shamt_nbits ) )
    s.out   = ValuePort( Type ) 

    @s.update
    def up_lshifter():
      s.out = s.in_ << s.shamt

  def line_trace( s ):  pass

# Adder 

class Adder( UpdatesImpl ):

  def __init__( s, Type ):
    s.in0 = ValuePort( Type )
    s.in1 = ValuePort( Type )
    s.out = ValuePort( Type )

    @s.update
    def up_adder():
      s.out = s.in0 + s.in1

  def line_trace( s ):  pass

# Subtractor

class Subtractor( UpdatesImpl ):

  def __init__( s, Type ):
    s.in0 = ValuePort( Type )
    s.in1 = ValuePort( Type )
    s.out = ValuePort( Type )

    @s.update
    def up_subtractor():
      s.out = s.in0 - s.in1

  def line_trace( s ):  pass

# ZeroComparator 

class ZeroComp( UpdatesImpl ):

  def __init__( s, Type ):
    s.in_ = ValuePort( Type )
    s.out = ValuePort( Bits1 )

    @s.update
    def up_zerocomp():
      s.out = Bits1( s.in_ == 0 )

  def line_trace( s ):  pass

# LeftThanComparator

class LTComp( UpdatesImpl ):

  def __init__( s, Type ):
    s.in0 = ValuePort( Type )
    s.in1 = ValuePort( Type )
    s.out = ValuePort( Bits1 )

    @s.update
    def up_ltcomp():
      s.out = Bits1(s.in0 < s.in1)

  def line_trace( s ):  pass

# LeftThanOrEqualToComparator

class LEComp( UpdatesImpl ):

  def __init__( s, Type ):
    s.in0 = ValuePort( Type )
    s.in1 = ValuePort( Type )
    s.out = ValuePort( Bits1 )

    @s.update
    def up_lecomp():
      s.out = Bits1(s.in0 <= s.in1)

  def line_trace( s ):  pass
