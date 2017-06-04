#-------------------------------------------------------------------------
# SimUpdateOnlyPass
#-------------------------------------------------------------------------
from pymtl.passes import BasePass, BasicElaborationPass, BasicConstraintPass, \
                         ScheduleUpblkPass, GenerateTickPass

from pymtl import UpdateOnly

class SimUpdateOnlyPass( BasePass ):

  def __init__( self, dump = False, tick_mode = 'unroll' ):
    self.dump = dump
    self.tick_mode = tick_mode

  def execute( self, m ):
    assert isinstance( m, UpdateOnly )
    m = BasicElaborationPass().execute( m )

    m = BasicConstraintPass( dump=self.dump ).execute( m )
    m = ScheduleUpblkPass  ( dump=self.dump ).execute( m )
    m = GenerateTickPass   ( dump=self.dump, mode=self.tick_mode ).execute( m )
    return m
