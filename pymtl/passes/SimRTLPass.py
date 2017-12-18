from pymtl.model import RTLComponent
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
