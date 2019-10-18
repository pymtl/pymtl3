from pymtl3 import *

# N-input Mux

class Mux( Component ):

  def construct( s, Type, ninputs ):
    s.in_ = [ InPort( Type ) for _ in range(ninputs) ]
    s.sel = InPort( int if Type is int else mk_bits( clog2(ninputs) ) )
    s.out = OutPort( Type )

    @s.update
    def up_mux():
      s.out = s.in_[ s.sel ]

# Rshifter

class RShifter( Component ):

  def construct( s, Type, shamt_nbits = 1 ):
    s.in_   = InPort( Type )
    s.shamt = InPort( int if Type is int else mk_bits( shamt_nbits ) )
    s.out   = OutPort( Type )

    @s.update
    def up_rshifter():
      s.out = s.in_ >> s.shamt

# Lshifter

class LShifter( Component ):

  def construct( s, Type, shamt_nbits = 1 ):
    s.in_   = InPort( Type )
    s.shamt = InPort( int if Type is int else mk_bits( shamt_nbits ) )
    s.out   = OutPort( Type )

    @s.update
    def up_lshifter():
      s.out = s.in_ << s.shamt

# Incrementer

class Incrementer( Component ):

  def construct( s, Type, amount=1 ):
    s.in_ = InPort( Type )
    s.out = OutPort( Type )

    @s.update
    def up_incrementer():
      s.out = s.in_ + Type(amount)

# Adder

class Adder( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( Type )

    @s.update
    def up_adder():
      s.out = s.in0 + s.in1

# And

class And( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( Type )

    @s.update
    def up_and():
      s.out = s.in0 & s.in1

# Subtractor

class Subtractor( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( Type )

    @s.update
    def up_subtractor():
      s.out = s.in0 - s.in1

# ZeroComparator

class ZeroComp( Component ):

  def construct( s, Type ):
    s.in_ = InPort( Type )
    s.out = OutPort( bool if Type is int else Bits1 )

    @s.update
    def up_zerocomp():
      # s.out = Bits1( s.in_ == Type(0) )
      s.out = s.in_ == Type(0)

# LeftThanComparator

class LTComp( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( bool if Type is int else Bits1 )

    @s.update
    def up_ltcomp():
      s.out = Bits1(s.in0 < s.in1)

# LeftThanOrEqualToComparator

class LEComp( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( bool if Type is int else Bits1 )

    @s.update
    def up_lecomp():
      s.out = Bits1(s.in0 <= s.in1)
