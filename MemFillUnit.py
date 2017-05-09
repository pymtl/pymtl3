from pymtl import *
from pclib.ifcs import MemIfcCL, MemIfcFL
from pclib.test import TestMemoryFL

class MemFillFL( MethodsAdapt ):
  def __init__( s, base_addr=0x1000, size=100 ):
    s.memifc = MemIfcFL()

    s.finished = False

    @s.update
    def up_fill():

      # Stream the writes

      for i in xrange(size):
        s.memifc.write( base_addr+(i<<2), 4, i )

      # Check the answers

      for i in xrange(size):
        assert s.memifc.read( base_addr+(i<<2), 4 ) == i
        print "#{} passed".format( i )

      s.finished = True

  def done( s ):
    return s.finished

class Harness( MethodsAdapt ):
  def __init__( s, level='fl', base_addr=0x1000, size=100 ):

    s.mem = TestMemoryFL()

    if   level == 'fl' : s.fill = MemFillFL( base_addr, size )( memifc = s.mem.ifc )
    elif level == 'cl' : s.fill = MemFillCL( base_addr, size )
    elif level == 'rtl': s.fill = MemFillRTL( base_addr, size )

  def done( s ):
    return s.fill.done()

if __name__ == "__main__":
  A = Harness( 'fl', base_addr = 0x100, size = 100 )
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
