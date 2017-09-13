#-------------------------------------------------------------------------
# RTLComponent
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.model import RTLComponent
from errors import ModelTypeError

from BasePass import BasePass
from ScheduleUpblkPass import ScheduleUpblkPass
from GenerateTickPass import GenerateTickPass
from SignalCleanupPass import SignalCleanupPass
from PrintMetadataPass import PrintMetadataPass

class SimRTLPass( BasePass ):

  def apply( self, m, mode='unroll' ):
    if not isinstance( m, RTLComponent ):
      raise ModelTypeError( "RTLComponent" )

    m.elaborate()

    ScheduleUpblkPass().apply( m )
    GenerateTickPass ( mode ).apply( m )
    SignalCleanupPass().apply( m )
