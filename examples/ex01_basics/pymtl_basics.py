"""
==========================================================================
pymtl_basics.py
==========================================================================
Basic tutorial about pymtl3 basics, such as update block, constraints,
method ports, etc.

Author : Yanghui Ou
  Date : June 15, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *

#-------------------------------------------------------------------------
# Model an incrementer using python variables
#-------------------------------------------------------------------------

class IncrPyVar( Component ):
  def construct( s, verbose=True ):

    s.incr_input = 10

    s.buf1 = 0
    s.buf2 = 0

    s.incr_output = 0

    # UpA writes data to buf1
    @s.update
    def upA():
      s.buf1 = s.incr_input
      s.incr_input += 10
    
    # UpB read data from buf1, increment it by 1, and write to buf2.
    @s.update
    def upB():
      s.buf2 = s.buf1 + 1
    
    # UpC read data from buf2.
    @s.update
    def upC():
      s.incr_output = s.buf2

    s.add_constraints( U(upA) < U(upB) )
    s.add_constraints( U(upB) < U(upC) )

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( s.buf1, s.buf2 )

#-------------------------------------------------------------------------
# Simulate the incrementer
#-------------------------------------------------------------------------

def test_pyvar():
  incr = IncrPyVar()
  incr.apply( SimpleSim )
  
  print( "\n==== Schedule ====" )
  for blk in incr._sched.schedule:
    if not blk.__name__.startswith('s'):
      print( blk.__name__ )

  print( "\n==== Line trace ====" )
  print( "   buf1    buf2")
  for i in range( 6 ):
    incr.tick()
    print("{:2}: {}".format( i, incr.line_trace() ))

#-------------------------------------------------------------------------
# Model an incrementer using RTL wires
#-------------------------------------------------------------------------

class IncrRTL( Component ):
  def construct( s, verbose=True ):
    
    s.incr_input = 10

    s.buf1 = Wire( int )
    s.buf2 = Wire( int )
    
    s.incr_output = 0

    # UpA writes data to buf1
    @s.update
    def upA():
      s.buf1 = s.incr_input
      s.incr_input += 10
    
    # UpB read data from buf1, increment it by 1, and write to buf2.
    @s.update
    def upB():
      s.buf2 = s.buf1 + 1
    
    # UpC read data from buf2.
    @s.update
    def upC():
      s.incr_output = s.buf2

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( s.buf1, s.buf2 )

#-------------------------------------------------------------------------
# Simulate the incrementer
#-------------------------------------------------------------------------

def test_rtl():
  incr = IncrRTL()
  incr.apply( SimpleSim )
  
  print( "\n==== Schedule ====" )
  for blk in incr._sched.schedule:
    if not blk.__name__.startswith('s'):
      print( blk.__name__ )

  print( "\n==== Line trace ====" )
  print( "   buf1    buf2")
  for i in range( 6 ):
    incr.tick()
    print( "{:2}: {}".format( i, incr.line_trace() ) )

#-------------------------------------------------------------------------
# Create an incrementer module using value ports
#-------------------------------------------------------------------------

class IncrModuleRTL( Component ):
  def construct( s ):

    s.in_ = InPort ( int )
    s.out = OutPort( int )
    
    s.buf1 = Wire( int )
    s.buf2 = Wire( int )

    s.connect( s.in_, s.buf1 )
    s.connect( s.out, s.buf2 )

    @s.update
    def upB():
      s.out = s.in_ + 1

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( s.in_, s.out )

#-------------------------------------------------------------------------
# Simulate the incrementer module with a test bench
#-------------------------------------------------------------------------

def test_tb_rtl():
  class TestBenchRTL( Component ):
    def construct( s ):
      s.incr_input = 10
      s.incr = IncrModuleRTL()      
      s.incr_output = 0

      # UpA writes data to input
      @s.update
      def upA():
        s.incr.in_ = s.incr_input
        s.incr_input += 10
      
      # UpC read data from output
      @s.update
      def upC():
        s.incr_output = s.incr.out

    def line_trace( s ):
      return "{:2} (+1) {:2}".format( s.incr.in_, s.incr.out )

  tb = TestBenchRTL()
  tb.apply( SimpleSim )

  print( "\n==== Schedule ====" )
  for blk in tb._sched.schedule:
    if not blk.__name__.startswith('s'):
      print( blk.__name__ )

  print( "\n==== Line trace ====" )
  print( "   in_     out")
  for i in range( 6 ):
    tb.tick()
    print( "{:2}: {}".format( i, tb.line_trace() ) )

#-------------------------------------------------------------------------
# Model an incrementer using methods
#-------------------------------------------------------------------------

class BufferObjCL( object ):
  def __init__( s ):
    s.data = 0
   
  def write( s, value ):
    s.data = value

  def read( s ):
    return s.data

class IncrObjCL( Component ):
  def construct( s, verbose=True ):

    s.incr_input = 10

    s.buf1 = BufferObjCL() 
    s.buf2 = BufferObjCL()

    s.incr_output = 0
    
    # UpA writes data to buf1
    @s.update
    def upA():
      s.buf1.write( s.incr_input )
      s.incr_input += 10

    # UpB read data from buf1, increment it by 1, and write to buf2.
    @s.update
    def upB():
      tmp = s.buf1.read()
      s.buf2.write( tmp+1 )
    
    # UpC read data from buf2.
    @s.update
    def upC():
      s.incr_output = s.buf2.read()

    s.add_constraints( U(upA) < U(upB) )
    s.add_constraints( U(upB) < U(upC) )

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( s.buf1.data, s.buf2.data )

#-------------------------------------------------------------------------
# Simulate the incrementer with python objects 
#-------------------------------------------------------------------------

def test_obj_cl():
  incr = IncrObjCL()
  incr.apply( SimpleSim )

  # FIXME: ignore s_reset__2 and s_clk__2?
  print( "\n==== Schedule ====" )
  for blk in incr._sched.schedule:
    if not blk.__name__.startswith('s'):
      print( blk.__name__ )

  print( "\n==== Line trace ====" )
  print( "   buf1    buf2")
  for i in range( 6 ):
    incr.tick()
    print("{:2}: {}".format( i, incr.line_trace() ))

#-------------------------------------------------------------------------
# Model an incrementer using methods
#-------------------------------------------------------------------------

class BufferCompCL( Component ):
  def construct( s ):
    s.data = 0
    s.add_constraints( M( s.read ) < M( s.write ) )
   
  @method_port
  def write( s, value ):
    s.data = value

  @method_port
  def read( s ):
    return s.data

class IncrCompCL( Component ):
  def construct( s, verbose=True ):

    s.incr_input = 10

    s.buf1 = BufferCompCL() 
    s.buf2 = BufferCompCL()

    s.incr_output = 0
    
    # UpA writes data to buf1
    @s.update
    def upA():
      s.buf1.write( s.incr_input )
      s.incr_input += 10

    # UpB read data from buf1, increment it by 1, and write to buf2.
    @s.update
    def upB():
      tmp = s.buf1.read()
      s.buf2.write( tmp+1 )
    
    # UpC read data from buf2.
    @s.update
    def upC():
      s.incr_output = s.buf2.read()

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( s.buf1.data, s.buf2.data )

#-------------------------------------------------------------------------
# Simulate the incrementer with CL component
#-------------------------------------------------------------------------

def test_comp_cl():
  incr = IncrCompCL()
  incr.apply( SimpleSim )

  # FIXME: ignore s_reset__2 and s_clk__2?
  print( "\n==== Schedule ====" )
  for blk in incr._sched.schedule:
    if not blk.__name__.startswith('s'):
      print( blk.__name__ )

  print( "\n==== Line trace ====" )
  print( "   buf1    buf2")
  for i in range( 6 ):
    incr.tick()
    print("{:2}: {}".format( i, incr.line_trace() ))

#-------------------------------------------------------------------------
# Create an incrementer module using method ports
#-------------------------------------------------------------------------

class IncrModuleCL( Component ):
  def construct( s ):

    s.write = CalleePort()
    s.read  = CalleePort()
    
    s.buf1 = BufferCompCL()
    s.buf2 = BufferCompCL()

    s.connect( s.write, s.buf1.write )
    s.connect( s.read,  s.buf2.read  )

    @s.update
    def upB():
      tmp = s.buf1.read()
      s.buf2.write( tmp+1 )

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( s.buf1.data, s.buf2.data )

#-------------------------------------------------------------------------
# Simulate the incrementer module with a test bench
#-------------------------------------------------------------------------

def test_tb_cl():
  class TestBenchCL( Component ):
    def construct( s ):
      s.incr_input  = 10
      s.incr        = IncrModuleCL()      
      s.incr_output = 0

      # UpA writes data to input
      @s.update
      def upA():
        s.incr.write( s.incr_input )
        s.incr_input += 10
      
      # UpC read data from output
      @s.update
      def upC():
        s.incr_output = s.incr.read()

    def line_trace( s ):
      return "{:2} (+1) {:2}".format( s.incr.buf1.data, s.incr.buf2.data )

  tb = TestBenchCL()
  tb.apply( SimpleSim )

  print( "\n==== Schedule ====" )
  for blk in tb._sched.schedule:
    if not blk.__name__.startswith('s'):
      print( blk.__name__ )

  print( "\n==== Line trace ====" )
  print( "   in_     out")
  for i in range( 6 ):
    tb.tick()
    print( "{:2}: {}".format( i, tb.line_trace() ) )
