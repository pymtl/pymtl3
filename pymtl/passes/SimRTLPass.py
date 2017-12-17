from pymtl.model import RTLComponent
from BasePass import BasePass
from GenDAGPass import GenDAGPass

class SimRTLPass( BasePass ):

  def __call__( self, top ):
    if not isinstance( top, RTLComponent ):
      raise ModelTypeError( "RTLComponent" )

    top.elaborate()

    GenDAGPass()( top )
    SimpleScheduleTickPass()( top )
    SignalCleanupPass()( top )
