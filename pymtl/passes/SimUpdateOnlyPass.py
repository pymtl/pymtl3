#-------------------------------------------------------------------------
# SimUpdateOnlyPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import BasePass, BasicElaborationPass, BasicConstraintPass, \
                         ScheduleUpblkPass, GenerateTickPass

from pymtl.components import UpdateOnly
from errors import ModelTypeError

class SimUpdateOnlyPass( BasePass ):

  def __init__( self, dump = False, tick_mode = 'unroll' ):
    self.dump = dump
    self.tick_mode = tick_mode

  def execute( self, m ):
    if not isinstance( m, UpdateOnly ):
      raise ModelTypeError( "UpdateOnly" )

    m = BasicElaborationPass().execute( m )

    m = BasicConstraintPass( dump=self.dump ).execute( m )
    m = ScheduleUpblkPass  ( dump=self.dump ).execute( m )
    m = GenerateTickPass   ( dump=self.dump, mode=self.tick_mode ).execute( m )
    return m
