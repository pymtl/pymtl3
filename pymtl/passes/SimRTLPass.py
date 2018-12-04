#=========================================================================
# SimRTLPass.py
#=========================================================================
# The model can be simulated (ticked) after applying this pass.
#
# Author : Shunning Jiang
# Date   : Dec 18, 2017

from pymtl.dsl.RTLComponent import RTLComponent
from BasePass import BasePass
from GenDAGPass import GenDAGPass
from SimpleSchedTickPass import SimpleSchedTickPass

class SimRTLPass( BasePass ):

  def __call__( self, top ):
    if not isinstance( top, RTLComponent ):
      raise ModelTypeError( "RTLComponent" )

    top.elaborate()

    GenDAGPass()( top ) # generate update block constraint graph
    SimpleSchedTickPass()( top ) # generate tick using simple scheduling

    top.lock_in_simulation()
