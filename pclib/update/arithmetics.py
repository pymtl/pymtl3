from pymtl import *

# N-input Mux

class Mux(Updates):

  def __init__( s, ninputs ):
    s.in_ = [ ValuePort(int) for _ in xrange(ninputs) ]
    s.sel = ValuePort(int)
    s.out = ValuePort(int)

    @s.update
    def up_mux():
      s.out = s.in_[ s.sel ]

  def line_trace( s ):  pass

# Rshifter

class RShifter(Updates):

  def __init__( s, nbits = 1, shamt_nbits = 1 ):
    s.in_   = ValuePort(int)
    s.shamt = ValuePort(int)
    s.out   = ValuePort(int)

    @s.update
    def up_rshifter():
      s.out = s.in_ >> s.shamt

  def line_trace( s ):  pass

# Lshifter

class LShifter(Updates):

  def __init__( s, nbits = 1, shamt_nbits = 1 ):
    s.in_   = ValuePort(int)
    s.shamt = ValuePort(int)
    s.out   = ValuePort(int) 

    @s.update
    def up_lshifter():
      s.out = s.in_ << s.shamt

  def line_trace( s ):  pass

# Adder 

class Adder(Updates):

  def __init__( s, nbits = 1 ):
    s.in0 = ValuePort(int)
    s.in1 = ValuePort(int)
    s.out = ValuePort(int)

    @s.update
    def up_adder():
      s.out = s.in0 + s.in1

  def line_trace( s ):  pass

# Subtractor

class Subtractor(Updates):

  def __init__( s, nbits = 1 ):
    s.in0 = ValuePort(int)
    s.in1 = ValuePort(int)
    s.out = ValuePort(int)

    @s.update
    def up_subtractor():
      s.out = s.in0 - s.in1

  def line_trace( s ):  pass

# ZeroComparator 

class ZeroComp(Updates):

  def __init__( s, nbits = 1 ):
    s.in_ = ValuePort(int)
    s.out = ValuePort(int)

    @s.update
    def up_zerocomp():
      s.out = (s.in_ == 0)

  def line_trace( s ):  pass

# LeftThanComparator

class LTComp(Updates):

  def __init__( s, nbits = 1 ):
    s.in0 = ValuePort(int)
    s.in1 = ValuePort(int)
    s.out = ValuePort(int)

    @s.update
    def up_ltcomp():
      s.out = (s.in0 < s.in1)

  def line_trace( s ):  pass

# LeftThanOrEqualToComparator

class LEComp(Updates):

  def __init__( s, nbits = 1 ):
    s.in0 = ValuePort(int)
    s.in1 = ValuePort(int)
    s.out = ValuePort(int)

    @s.update
    def up_lecomp():
      s.out = (s.in0 <= s.in1)

  def line_trace( s ):  pass
