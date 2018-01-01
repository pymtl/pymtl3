from pymtl import *

# N-input Mux

class Mux( RTLComponent ):

  def construct( s, Type, ninputs ):
    s.in_ = [ InVPort( Type ) for _ in xrange(ninputs) ]
    s.sel = InVPort( int if Type is int else mk_bits( clog2(ninputs) ) )
    s.out = OutVPort( Type )

    @s.update
    def up_mux():
      s.out = s.in_[ s.sel ]

# Rshifter

class RShifter( RTLComponent ):

  def construct( s, Type, shamt_nbits = 1 ):
    s.in_   = InVPort( Type )
    s.shamt = InVPort( int if Type is int else mk_bits( shamt_nbits ) )
    s.out   = OutVPort( Type )

    @s.update
    def up_rshifter():
      s.out = s.in_ >> s.shamt

# Lshifter

class LShifter( RTLComponent ):

  def construct( s, Type, shamt_nbits = 1 ):
    s.in_   = InVPort( Type )
    s.shamt = InVPort( int if Type is int else mk_bits( shamt_nbits ) )
    s.out   = OutVPort( Type ) 

    @s.update
    def up_lshifter():
      s.out = s.in_ << s.shamt

# Incrementer 

class Incrementer( RTLComponent ):

  def construct( s, Type, amount=1 ):
    s.in_ = InVPort( Type )
    s.out = OutVPort( Type )

    @s.update
    def up_incrementer():
      s.out = s.in_ + Type(amount)

# Adder 

class Adder( RTLComponent ):

  def construct( s, Type ):
    s.in0 = InVPort( Type )
    s.in1 = InVPort( Type )
    s.out = OutVPort( Type )

    @s.update
    def up_adder():
      s.out = s.in0 + s.in1

# Subtractor

class Subtractor( RTLComponent ):

  def construct( s, Type ):
    s.in0 = InVPort( Type )
    s.in1 = InVPort( Type )
    s.out = OutVPort( Type )

    @s.update
    def up_subtractor():
      s.out = s.in0 - s.in1

# ZeroComparator 

class ZeroComp( RTLComponent ):

  def construct( s, Type ):
    s.in_ = InVPort( Type )
    s.out = OutVPort( bool if Type is int else Bits1 )

    @s.update
    def up_zerocomp():
      s.out = Bits1( s.in_ == Type(0) )

# LeftThanComparator

class LTComp( RTLComponent ):

  def construct( s, Type ):
    s.in0 = InVPort( Type )
    s.in1 = InVPort( Type )
    s.out = OutVPort( bool if Type is int else Bits1 )

    @s.update
    def up_ltcomp():
      s.out = Bits1(s.in0 < s.in1)

# LeftThanOrEqualToComparator

class LEComp( RTLComponent ):

  def construct( s, Type ):
    s.in0 = InVPort( Type )
    s.in1 = InVPort( Type )
    s.out = OutVPort( bool if Type is int else Bits1 )

    @s.update
    def up_lecomp():
      s.out = Bits1(s.in0 <= s.in1)
