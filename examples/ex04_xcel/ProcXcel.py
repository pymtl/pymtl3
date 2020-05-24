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
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL, SendIfcFL, GetIfcFL
from pymtl3.stdlib.mem import MemMasterIfcCL, MemMasterIfcFL, MemMasterIfcRTL, mk_mem_msg


class ProcXcel( Component ):

  def construct( s, ProcClass, XcelClass ):

    req_class, resp_class = mk_mem_msg( 8, 32, 32 )

    s.commit_inst = OutPort( Bits1 )

    # Instruction Memory Request/Response Interface

    s.proc = ProcClass()
    s.proc.commit_inst //= s.commit_inst

    s.xcel = XcelClass()
    s.xcel.xcel //= s.proc.xcel

    if   isinstance( s.proc.imem, MemMasterIfcRTL ): # RTL proc
      s.mngr2proc = RecvIfcRTL( Bits32 )
      s.proc2mngr = SendIfcRTL( Bits32 )
      s.imem = MemMasterIfcRTL( req_class, resp_class )
      s.dmem = MemMasterIfcRTL( req_class, resp_class )

    elif isinstance( s.proc.imem, MemMasterIfcCL ): # CL proc
      s.mngr2proc = CalleeIfcCL( Type=Bits32 )
      s.proc2mngr = CallerIfcCL( Type=Bits32 )
      s.imem = MemMasterIfcCL( req_class, resp_class )
      s.dmem = MemMasterIfcCL( req_class, resp_class )

    elif isinstance( s.proc.imem, MemMasterIfcFL ): # FL proc
      s.mngr2proc = GetIfcFL( Type=Bits32 )
      s.proc2mngr = SendIfcFL( Type=Bits32 )
      s.imem = MemMasterIfcFL()
      s.dmem = MemMasterIfcFL()


    s.mngr2proc //= s.proc.mngr2proc
    s.proc2mngr //= s.proc.proc2mngr
    s.imem      //= s.proc.imem
    s.dmem      //= s.proc.dmem

  def line_trace( s ):
    return "{}|{}".format( s.proc.line_trace(), s.xcel.line_trace() )
