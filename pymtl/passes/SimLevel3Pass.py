#-------------------------------------------------------------------------
# SimLevel3Pass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.model import ComponentLevel3
from errors import ModelTypeError

from BasePass import BasePass
from ScheduleUpblkPass import ScheduleUpblkPass
from GenerateTickPass import GenerateTickPass
from SignalCleanupPass import SignalCleanupPass
from PrintMetadataPass import PrintMetadataPass

class SimLevel3Pass( BasePass ):

  def apply( self, m, mode='unroll' ):
    if not isinstance( m, ComponentLevel3 ):
      raise ModelTypeError( "ComponentLevel3" )

    m.elaborate()

    ScheduleUpblkPass().apply( m )
    GenerateTickPass ( mode ).apply( m )
    SignalCleanupPass().apply( m )
