#-------------------------------------------------------------------------
# SimUpdateVarNetPass
#-------------------------------------------------------------------------
from pymtl.passes import SimUpdateOnlyPass, VarNetElaborationPass, VarConstraintPass, \
                         SignalTypeCheckPass, GenerateNetUpblkPass, ScheduleUpblkPass, \
                         GenerateTickPass, SignalCleanupPass

from pymtl.components import UpdateVarNet

class SimUpdateVarNetPass( SimUpdateOnlyPass ):

  def execute( self, m ):
    assert isinstance( m, UpdateVarNet )

    m = VarNetElaborationPass( dump=self.dump ).execute( m )
    m = SignalTypeCheckPass().execute( m )

    m = GenerateNetUpblkPass().execute( m )

    m = VarConstraintPass( dump=self.dump ).execute( m )
    m = ScheduleUpblkPass( dump=self.dump ).execute( m )
    m = GenerateTickPass ( dump=self.dump, mode=self.tick_mode ).execute( m )

    m = SignalCleanupPass().execute( m )

    return m
