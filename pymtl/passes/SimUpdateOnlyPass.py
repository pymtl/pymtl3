#-------------------------------------------------------------------------
# SimUpdateOnlyPass
#-------------------------------------------------------------------------
from pymtl.passes import BasePass, TagNamePass, BasicElaborationPass, \
                         ScheduleUpblkPass, GenerateTickPass, BasicConstraintPass

class SimUpdateOnlyPass( BasePass ):

  def __init__( self, dump = False ):
    self.dump = dump

  def execute( self, m ):
    m = BasicElaborationPass().execute( m )

    m = BasicConstraintPass().execute( m )
    m = ScheduleUpblkPass( dump=self.dump ).execute( m )
    m = GenerateTickPass( dump=self.dump ).execute( m )
    return m
