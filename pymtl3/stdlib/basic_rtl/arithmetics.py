from pymtl3 import *

# N-input Mux

class Mux( Component ):

  def construct( s, Type, ninputs ):
    assert ninputs > 0
    s.in_ = [ InPort( Type ) for _ in range(ninputs) ]
    s.out = OutPort( Type )
    s.sel = InPort( max(1, clog2(ninputs)) ) # allow 1-input

    @update
    def up_mux():
      s.out @= s.in_[ s.sel ]

# N-output Demux

class Demux( Component ):

  def construct( s, Type, noutputs ):
    assert noutputs > 0
    s.in_ = InPort( Type )
    s.out = [ OutPort( Type ) for _ in range(noutputs) ]
    s.sel = InPort( max(1, clog2(noutputs)) ) # allow 1-input

    default_value = Type()

    @update
    def up_mux():
      for i in range(noutputs):
        s.out[i] @= default_value
      s.out[ s.sel ] @= s.in_

# Rshifter

class RightLogicalShifter( Component ):

  def construct( s, Type, shamt_nbits=1 ):
    s.in_   = InPort( Type )
    s.shamt = InPort( shamt_nbits )
    s.out   = OutPort( Type )
    assert shamt_nbits == Type.nbits

    @update
    def up_rshifter():
      s.out @= s.in_ >> s.shamt

# Lshifter

class LeftLogicalShifter( Component ):

  def construct( s, Type, shamt_nbits = 1 ):
    s.in_   = InPort( Type )
    s.shamt = InPort( shamt_nbits )
    s.out   = OutPort( Type )
    assert shamt_nbits == Type.nbits

    @update
    def up_lshifter():
      s.out @= s.in_ << s.shamt

# Incrementer

class Incrementer( Component ):

  def construct( s, Type, amount=1 ):
    s.in_ = InPort( Type )
    s.out = OutPort( Type )

    @update
    def up_incrementer():
      s.out @= s.in_ + amount

# Adder

class Adder( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( Type )

    @update
    def up_adder():
      s.out @= s.in0 + s.in1

# And

class And( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( Type )

    @update
    def up_and():
      s.out @= s.in0 & s.in1

# Subtractor

class Subtractor( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( Type )

    @update
    def up_subtractor():
      s.out @= s.in0 - s.in1

# ZeroComparator

class ZeroComparator( Component ):

  def construct( s, Type ):
    s.in_ = InPort( Type )
    s.out = OutPort()

    @update
    def up_zerocomp():
      s.out @= s.in_ == 0

# LeftThanComparator

class LTComparator( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort()

    @update
    def up_ltcomp():
      s.out @= s.in0 < s.in1

# LeftThanOrEqualToComparator

class LEComparator( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort()

    @update
    def up_lecomp():
      s.out @= s.in0 <= s.in1

# EqComparator

class EqComparator( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort()

    @update
    def up_lecomp():
      s.out @= s.in0 == s.in1
