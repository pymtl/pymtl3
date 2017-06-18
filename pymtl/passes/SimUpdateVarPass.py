#-------------------------------------------------------------------------
# SimUpdateVarPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import SimUpdateOnlyPass, \
                         SignalTypeCheckPass, ScheduleUpblkPass, GenerateTickPass, \
                         SignalCleanupPass

from pymtl.components import UpdateVar
from errors import ModelTypeError

class SimUpdateVarPass( SimUpdateOnlyPass ):

  def apply( self, m ):
    if not isinstance( m, UpdateVar ):
      raise ModelTypeError( "UpdateVar" )

    m.elaborate()

    ScheduleUpblkPass().apply( m )
    GenerateTickPass ( mode=self.tick_mode ).apply( m )
    SignalCleanupPass().apply( m )
