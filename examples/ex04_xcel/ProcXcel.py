"""
==========================================================================
 ProcRTL.py
==========================================================================
TinyRV0 RTL proc

Author : Shunning Jiang
  Date : June 12, 2019
"""

from pymtl3 import *
from pymtl3.stdlib.ifcs.mem_ifcs  import MemMasterIfcRTL, MemMasterIfcCL, MemMasterIfcFL
from pymtl3.stdlib.ifcs  import SendIfcRTL, RecvIfcRTL

from pymtl3.stdlib.ifcs import mk_mem_msg

class ProcXcel( Component ):

  def construct( s, proc_cls, xcel_cls ):

    req_class, resp_class = mk_mem_msg( 8, 32, 32 )

    s.commit_inst = OutPort( Bits1 )

    # Instruction Memory Request/Response Interface

    s.proc = proc_cls()( commit_inst = s.commit_inst )
    s.xcel = xcel_cls()( xcel = s.proc.xcel )

    if   isinstance( s.proc.imem, MemMasterIfcRTL ): # RTL proc
      s.mngr2proc = RecvIfcRTL( Bits32 )
      s.proc2mngr = SendIfcRTL( Bits32 )
      s.imem = MemMasterIfcRTL( req_class, resp_class )
      s.dmem = MemMasterIfcRTL( req_class, resp_class )

    elif isinstance( s.proc.imem, MemMasterIfcCL ): # CL proc
      s.mngr2proc = NonBlockingCalleeIfc( Bits32 )
      s.proc2mngr = NonBlockingCallerIfc( Bits32 )
      s.imem = MemMasterIfcCL( req_class, resp_class )
      s.dmem = MemMasterIfcCL( req_class, resp_class )

    elif isinstance( s.proc.imem, MemMasterIfcFL ): # CL proc
      s.mngr2proc = NonBlockingCalleeIfc( Bits32 )
      s.proc2mngr = NonBlockingCallerIfc( Bits32 )
      s.imem = MemMasterIfcCL( req_class, resp_class )
      s.dmem = MemMasterIfcCL( req_class, resp_class )

    s.connect_pairs(
      s.mngr2proc, s.proc.mngr2proc,
      s.proc2mngr, s.proc.proc2mngr,
      s.imem,      s.proc.imem,
      s.dmem,      s.proc.dmem,
    )

  def line_trace( s ):
    return "{}|{}".format( s.proc.line_trace(), s.xcel.line_trace() )
