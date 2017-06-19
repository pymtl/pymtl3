#-------------------------------------------------------------------------
# SimUpdateVarNetPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import SimUpdateVarPass, ScheduleUpblkPass, \
                         GenerateTickPass, SignalCleanupPass

from pymtl.components import UpdateVarNet
from errors import ModelTypeError

class SimUpdateVarNetPass( SimUpdateVarPass ):

  def apply( self, m ):
    if not isinstance( m, UpdateVarNet ):
      raise ModelTypeError( "UpdateVarNet" )

    m.elaborate()

    ScheduleUpblkPass().apply( m )
    GenerateTickPass ( mode=self.tick_mode ).apply( m )
    SignalCleanupPass().apply( m )
