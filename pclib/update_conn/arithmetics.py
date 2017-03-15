from pymtl import *

# N-input Mux

class Mux(UpdatesConnection):

  def __init__( s, ninputs ):
    s.in_ = [ ValuePort(int) for _ in xrange(ninputs) ]
    s.sel = ValuePort(int)
    s.out = ValuePort(int)

    @s.update
    def up_mux():
      s.out = s.in_[ s.sel ]

    for x in s.in_:
      s.add_constraints(
        WR(x) < U(up_mux),
      )

    s.add_constraints(
      WR(s.sel) < U(up_mux),
      U(up_mux) < RD(s.out),
    )

  def line_trace( s ):  pass

# Rshifter

class RShifter(UpdatesConnection):

  def __init__( s, nbits = 1, shamt_nbits = 1 ):
    s.in_ = s.shamt = s.out = 0

    @s.update
    def up_rshifter():
      s.out = s.in_ >> s.shamt

  def line_trace( s ):  pass

# Lshifter

class LShifter(UpdatesConnection):

  def __init__( s, nbits = 1, shamt_nbits = 1 ):
    s.in_ = s.shamt = s.out = 0

    @s.update
    def up_lshifter():
      s.out = s.in_ << s.shamt

  def line_trace( s ):  pass

# Adder 

class Adder(UpdatesConnection):

  def __init__( s, nbits = 1, ninputs = 2 ):
    s.in_ = [ 0 ] * ninputs
    s.out = 0

    @s.update
    def up_adder():
      s.out = 0
      for i in xrange(ninputs):
        s.out += s.in_[i]

  def line_trace( s ):  pass

# Subtractor

class Subtractor(UpdatesConnection):

  def __init__( s, nbits = 1 ):
    s.in0 = s.in1 = 0
    s.out = 0

    @s.update
    def up_adder():
      s.out = s.in0 - s.in1

  def line_trace( s ):  pass

# ZeroComparator 

class ZeroComp(UpdatesConnection):

  def __init__( s, nbits = 1 ):
    s.in_ = 0
    s.out = 0

    @s.update
    def up_zerocomp():
      s.out = (s.in_ == 0)

  def line_trace( s ):  pass

# LeftThanComparator

class LTComp(UpdatesConnection):

  def __init__( s, nbits = 1 ):
    s.in0 = s.in1 = 0
    s.out = 0

    @s.update
    def up_ltcomp():
      s.out = (s.in0 < s.in1)

  def line_trace( s ):  pass

# LeftThanOrEqualToComparator

class LEComp(UpdatesConnection):

  def __init__( s, nbits = 1 ):
    s.in0 = s.in1 = 0
    s.out = 0

    @s.update
    def up_lecomp():
      s.out = (s.in0 <= s.in1)

  def line_trace( s ):  pass
