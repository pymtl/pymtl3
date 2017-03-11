from pymtl import *

# N-input Mux

class Mux(UpdatesImpl):

  def __init__( s, nbits = 1 ):
    s.in_ = [0] * (1 << nbits)
    s.sel = 0
    s.out = 0

    @s.update
    def up_mux():
      s.out = s.in_[ s.sel ]

  def line_trace( s ):  pass

# Rshifter

class RShifter(UpdatesImpl):

  def __init__( s, nbits = 1, shamt_nbits = 1 ):
    s.in_ = s.shamt = s.out = 0

    @s.update
    def up_rshifter():
      s.out = s.in_ >> s.shamt

  def line_trace( s ):  pass

# Lshifter

class LShifter(UpdatesImpl):

  def __init__( s, nbits = 1, shamt_nbits = 1 ):
    s.in_ = s.shamt = s.out = 0

    @s.update
    def up_lshifter():
      s.out = s.in_ << s.shamt

  def line_trace( s ):  pass

# Adder 

class Adder(UpdatesImpl):

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

class Subtractor(UpdatesImpl):

  def __init__( s, nbits = 1 ):
    s.in0 = s.in1 = 0
    s.out = 0

    @s.update
    def up_adder():
      s.out = s.in0 - s.in1

  def line_trace( s ):  pass

# ZeroComparator 

class ZeroComp(UpdatesImpl):

  def __init__( s, nbits = 1 ):
    s.in_ = 0
    s.out = 0

    @s.update
    def up_zerocomp():
      s.out = (s.in_ == 0)

  def line_trace( s ):  pass

# LeftThanComparator

class LTComp(UpdatesImpl):

  def __init__( s, nbits = 1 ):
    s.in0 = s.in1 = 0
    s.out = 0

    @s.update
    def up_ltcomp():
      s.out = (s.in0 < s.in1)

  def line_trace( s ):  pass

# LeftThanOrEqualToComparator

class LEComp(UpdatesImpl):

  def __init__( s, nbits = 1 ):
    s.in0 = s.in1 = 0
    s.out = 0

    @s.update
    def up_lecomp():
      s.out = (s.in0 <= s.in1)

  def line_trace( s ):  pass
