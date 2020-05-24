"""
========================================================================
PortCheck_test.py
========================================================================

Author : Shunning Jiang
Date   : Dec 25, 2017
"""
from pymtl3.datatypes import Bits32
from pymtl3.dsl.ComponentLevel1 import update
from pymtl3.dsl.ComponentLevel3 import ComponentLevel3, connect
from pymtl3.dsl.Connectable import InPort, OutPort, Wire
from pymtl3.dsl.errors import InvalidConnectionError, SignalTypeError

from .sim_utils import simple_sim_pass


def _test_model( cls ):
  A = cls()
  A.elaborate()
  simple_sim_pass( A, 0x123 )

  for i in range(10):
    A.tick()

def test_illegal_inport_write():

  class B( ComponentLevel3 ):
    def construct( s ):
      s.in_ = InPort( Bits32 )

      @update
      def up_B_write():
        s.in_[1:10] @= 10

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.b = B()

  try:
    _test_model( Top )
  except SignalTypeError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown invalid input port write SignalTypeError.")

def test_illegal_inport_deep_write():

  class B( ComponentLevel3 ):
    def construct( s ):
      s.in_ = InPort( Bits32 )

      @update
      def up_B_print():
        print(s.in_)

  class BWrap( ComponentLevel3 ):
    def construct( s ):
      s.b = B()

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.b = BWrap()

      @update
      def up_write_b_in():
        s.b.b.in_[1:10] @= 10

  try:
    _test_model( Top )
  except SignalTypeError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown invalid input port write SignalTypeError.")

def test_legal_inport_write():

  class B( ComponentLevel3 ):
    def construct( s ):
      s.in_ = InPort( Bits32 )

      @update
      def up_B_print():
        print(s.in_)

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.b = B()

      @update
      def up_write_b_in():
        s.b.in_[1:10] @= 10

  _test_model( Top )

def test_illegal_outport_write():

  class A( ComponentLevel3 ):
    def construct( s ):
      s.out = OutPort( Bits32 )

      @update
      def up_A_read():
        print(s.out)

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.a = A()

      @update
      def up_write_a_out():
        s.a.out[1:10] @= 10

  try:
    _test_model( Top )
  except SignalTypeError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown invalid output port write SignalTypeError.")

def test_illegal_outport_deep_write():

  class A( ComponentLevel3 ):
    def construct( s ):
      s.out = OutPort( Bits32 )

      @update
      def up_A_read():
        print(s.out)

  class AWrap( ComponentLevel3 ):
    def construct( s ):
      s.a = A()

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.a = AWrap()

      @update
      def up_write_a_out():
        s.a.a.out[1:10] @= 10

  try:
    _test_model( Top )
  except SignalTypeError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown invalid output port write SignalTypeError.")

def test_legal_outport_write():

  class A( ComponentLevel3 ):
    def construct( s ):
      s.out = OutPort( Bits32 )

      @update
      def up_A_write():
        s.out[0:2] @= 2

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.a = A()

      @update
      def up_read_a_out():
        print(s.a.out)

  _test_model( Top )

def test_illegal_wire_write():

  class A( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire( Bits32 )

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.a = A()

      @update
      def up_write_a_out():
        s.a.wire[1:10] @= 10

  try:
    _test_model( Top )
  except SignalTypeError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown invalid wire write SignalTypeError.")

def test_illegal_wire_read():

  class A( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire( Bits32 )
      @update
      def up_write_wire():
        s.wire[1:10] @= 10

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.a = A()

      @update
      def up_read_a_out():
        print(s.a.wire[1:10])

  try:
    _test_model( Top )
  except SignalTypeError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown invalid wire write SignalTypeError.")

def test_legal_port_connect():

  class A( ComponentLevel3 ):
    def construct( s ):
      s.out = OutPort(32)

      @update
      def up_A_write():
        s.out @= 123

  class B( ComponentLevel3 ):
    def construct( s ):
      s.in_ = InPort(32)

      @update
      def up_B_read():
        print(s.in_)

  class OutWrap(ComponentLevel3):
    def construct( s ):
      s.out = OutPort(32)
      s.a = A()
      s.a.out //= s.out

      @update
      def up_out_read():
        print(s.out)

  class InWrap(ComponentLevel3):
    def construct( s ):
      s.in_ = InPort(32)
      s.b = B()
      s.b.in_ //= s.in_

      @update
      def up_in_read():
        print(s.in_)

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.i = InWrap()
      s.o = OutWrap()
      connect( s.o.out, s.i.in_ )

  _test_model( Top )

def test_illegal_same_host():

  class A( ComponentLevel3 ):
    def construct( s ):
      s.out = OutPort(32)
      @update
      def up_A_write():
        s.out @= 123

  class AWrap(ComponentLevel3):
    def construct( s ):
      s.out = OutPort(32) # Wire is the same
      s.a = A()
      s.a.out //= s.out

      s.in_ = InPort(32)

      connect( s.out, s.in_ )

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.awrap = AWrap()

  try:
    _test_model( Top )
  except InvalidConnectionError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidConnectionError.")

def test_illegal_rdhost_is_wrhost_parent():

  class A( ComponentLevel3 ):
    def construct( s ):
      s.out = OutPort(32)
      @update
      def up_A_write():
        s.out @= 123

  class AWrap(ComponentLevel3):
    def construct( s ):
      s.out = InPort(32) # Should be OutPort
      s.a   = A()
      s.a.out //= s.out

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.awrap = AWrap()

  try:
    _test_model( Top )
  except SignalTypeError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown invalid wire type SignalTypeError.")

def test_illegal_wrhost_is_rdhost_parent():

  class A( ComponentLevel3 ):
    def construct( s ):
      s.out = OutPort(32)
      @update
      def up_A_write():
        s.out @= 123

  class B( ComponentLevel3 ):
    def construct( s ):
      s.in_ = OutPort(32) # Should be InPort
      @update
      def up_B_read():
        print(s.in_)

  class BWrap(ComponentLevel3):
    def construct( s ):
      s.in_ = InPort(32)
      s.b   = B()
      s.b.in_ //= s.in_

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.a = A()
      s.b = BWrap()
      connect( s.a.out, s.b.in_ )

  try:
    _test_model( Top )
  except SignalTypeError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown invalid wire type SignalTypeError.")

def test_illegal_hosts_same_parent():

  class A( ComponentLevel3 ):
    def construct( s ):
      s.out = OutPort(32)
      @update
      def up_A_write():
        s.out @= 123

  class B( ComponentLevel3 ):
    def construct( s ):
      s.in_ = InPort(32)
      @update
      def up_B_read():
        print(s.in_)

  class BWrap(ComponentLevel3):
    def construct( s ):
      s.in_ = OutPort(32) # Should be InPort
      s.b   = B()
      s.b.in_ //= s.in_

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.a = A()
      s.b = BWrap()
      connect( s.a.out, s.b.in_ )

  try:
    _test_model( Top )
  except SignalTypeError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown invalid wire type SignalTypeError.")

def test_illegal_hosts_too_far():

  class A( ComponentLevel3 ):
    def construct( s ):
      s.out = OutPort(32)
      @update
      def up_A_write():
        s.out @= 123

  class AWrap( ComponentLevel3 ):
    def construct( s ):
      s.out = OutPort(32)
      s.A = A()
      s.A.out //= s.out

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire(32)
      s.A = AWrap()

      connect( s.wire, s.A.A.out )

  try:
    _test_model( Top )
  except SignalTypeError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown hosts too far SignalTypeError.")
