#-------------------------------------------------------------------------
# SimUpdateOnlyPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import BasePass, BasicElaborationPass, \
                         ScheduleUpblkPass, GenerateTickPass

from pymtl.components import UpdateOnly
from errors import ModelTypeError

class SimUpdateOnlyPass( BasePass ):

  def __init__( self, dump = False, tick_mode = 'unroll' ):
    self.dump = dump
    self.tick_mode = tick_mode

  def apply( self, m ):
    if not isinstance( m, UpdateOnly ):
      raise ModelTypeError( "UpdateOnly" )

    m.elaborate()
    ScheduleUpblkPass().apply( m )
    GenerateTickPass ( mode=self.tick_mode ).apply( m )
