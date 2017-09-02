#-------------------------------------------------------------------------
# SimLevel3Pass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import BasePass, ScheduleUpblkPass, GenerateTickPass, SignalCleanupPass

from pymtl.model import ComponentLevel3
from errors import ModelTypeError

class SimLevel3Pass( BasePass ):

  def apply( self, m, mode='unroll' ):
    if not isinstance( m, ComponentLevel3 ):
      raise ModelTypeError( "ComponentLevel3" )

    m.elaborate()

    ScheduleUpblkPass().apply( m )
    GenerateTickPass ( mode ).apply( m )
    SignalCleanupPass().apply( m )
