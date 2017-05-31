from pymtl import *
from pclib.rtl import TestBasicSource as TestSource, TestBasicSink as TestSink

def _test_model( model ):
  m = model()
  sim = SimLevel3( m )

  for i in xrange(10):
    sim.tick()

def test_illegal_inport_write():

  class B( UpdateConnect ):
    def __init__( s ):
      s.in_ = InVPort( Bits32 )

      @s.update
      def up_B_write():
        s.in_[1:10] = 10

  class Top( UpdateConnect ):
    def __init__( s ):
      s.b = B()

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown invalid input port write exception.")

def test_illegal_inport_deep_write():

  class B( UpdateConnect ):
    def __init__( s ):
      s.in_ = InVPort( Bits32 )

      @s.update
      def up_B_print():
        print s.in_

  class BWrap( UpdateConnect ):
    def __init__( s ):
      s.b = B()

  class Top( UpdateConnect ):
    def __init__( s ):
      s.b = BWrap()

      @s.update
      def up_write_b_in():
        s.b.b.in_[1:10] = 10

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown invalid input port write exception.")

def test_legal_inport_write():

  class B( UpdateConnect ):
    def __init__( s ):
      s.in_ = InVPort( Bits32 )

      @s.update
      def up_B_print():
        print s.in_

  class Top( UpdateConnect ):
    def __init__( s ):
      s.b = B()

      @s.update
      def up_write_b_in():
        s.b.in_[1:10] = 10

  _test_model( Top )

def test_illegal_outport_write():

  class A( UpdateConnect ):
    def __init__( s ):
      s.out = OutVPort( Bits32 )

      @s.update
      def up_A_read():
        print s.out

  class Top( UpdateConnect ):
    def __init__( s ):
      s.a = A()

      @s.update
      def up_write_a_out():
        s.a.out[1:10] = 10

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown invalid output port write exception.")

def test_illegal_outport_deep_write():

  class A( UpdateConnect ):
    def __init__( s ):
      s.out = OutVPort( Bits32 )

      @s.update
      def up_A_read():
        print s.out

  class AWrap( UpdateConnect ):
    def __init__( s ):
      s.a = A()

  class Top( UpdateConnect ):
    def __init__( s ):
      s.a = AWrap()

      @s.update
      def up_write_a_out():
        s.a.a.out[1:10] = 10

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown invalid output port write exception.")

def test_legal_outport_write():

  class A( UpdateConnect ):
    def __init__( s ):
      s.out = OutVPort( Bits32 )

      @s.update
      def up_A_write():
        s.out[0:2] = 2

  class Top( UpdateConnect ):
    def __init__( s ):
      s.a = A()

      @s.update
      def up_read_a_out():
        print s.a.out

  _test_model( Top )
