from pymtl import *

from pclib.update import TestSource
from pclib.update import TestSink

def test_connect_list_int_idx():

  class Mux( UpdatesCall ):
    def __init__( s, Type, sel_nbits ):
      s.in_ = [ ValuePort( Type ) for _ in xrange(1<<sel_nbits) ]
      s.sel = ValuePort( mk_bits( sel_nbits ) )
      s.out = ValuePort( Type )

      @s.update
      def up_mux():
        s.out = s.in_[ s.sel ]

  ZERO = 0

  class Top(UpdatesCall):

    def __init__( s ):

      s.src_in0 = TestSource( [4,3,2,1] )
      s.src_in1 = TestSource( [8,7,6,5] )
      s.src_sel = TestSource( [1,0,1,0] )
      s.sink    = TestSink  ( [8,3,6,1] )

      s.ONE = 1

      s.mux = Mux(int,1) (
        sel = s.src_sel.out,
        out = s.sink.in_,
        in_ = {
          ZERO  : s.src_in0.out,
          s.ONE : s.src_in1.out,
        },
      )

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  A = Top()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()

