"""
==========================================================================
 ProcXcel.py
==========================================================================
Processor-accelerator compostion.

Author : Shunning Jiang
  Date : June 12, 2019
"""

from pymtl3 import *
from pymtl3.stdlib.connects import connect_pairs
from pymtl3.stdlib.mem import mk_mem_msg
from pymtl3.stdlib.mem.ifcs import MemRequesterIfc
from pymtl3.stdlib.stream.ifcs import IStreamIfc, OStreamIfc


class ProcXcel( Component ):

  def construct( s, ProcClass, XcelClass ):

    req_class, resp_class = mk_mem_msg( 8, 32, 32 )

    s.commit_inst = OutPort( Bits1 )

    # Instruction Memory Request/Response Interface

    s.proc = ProcClass()
    s.proc.commit_inst //= s.commit_inst

    s.xcel = XcelClass()
    s.xcel.xcel //= s.proc.xcel

    assert isinstance( s.proc.imem, MemRequesterIfc )
    s.mngr2proc = IStreamIfc( Bits32 )
    s.proc2mngr = OStreamIfc( Bits32 )
    s.imem = MemRequesterIfc( req_class, resp_class )
    s.dmem = MemRequesterIfc( req_class, resp_class )

    s.mngr2proc //= s.proc.mngr2proc
    s.proc2mngr //= s.proc.proc2mngr
    s.imem      //= s.proc.imem
    s.dmem      //= s.proc.dmem

  def line_trace( s ):
    return "{}|{}".format( s.proc.line_trace(), s.xcel.line_trace() )
