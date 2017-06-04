#-------------------------------------------------------------------------
# SimUpdateWithVarPass
#-------------------------------------------------------------------------
from pymtl.passes import SimUpdateOnlyPass, VarElaborationPass, VarConstraintPass, \
                         ScheduleUpblkPass, GenerateTickPass, SignalCleanupPass

from pymtl.components import UpdateWithVar

class SimUpdateWithVarPass( SimUpdateOnlyPass ):

  def execute( self, m ):
    assert isinstance( m, UpdateWithVar )
    m = VarElaborationPass( dump=self.dump ).execute( m )

    m = VarConstraintPass( dump=self.dump ).execute( m )
    m = ScheduleUpblkPass( dump=self.dump ).execute( m )
    m = GenerateTickPass( dump=self.dump ).execute( m )

    m = SignalCleanupPass().execute( m )
    
    return m
