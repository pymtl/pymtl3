from ..BasePass import BasePass
from ..sim.GenDAGPass import GenDAGPass
from ..sim.SimpleSchedulePass import SimpleSchedulePass
from ..sim.WrapGreenletPass import WrapGreenletPass
from .HeuristicTopoPass import HeuristicTopoPass
from .TraceBreakingSchedTickPass import TraceBreakingSchedTickPass
from .UnrollTickPass import UnrollTickPass


class UnrollSim( BasePass ):
  def __call__( s, top ):
    top.elaborate()
    GenDAGPass()( top )
    WrapGreenletPass()( top )
    SimpleSchedulePass()( top )
    UnrollTickPass()( top )
    top.lock_in_simulation()

class HeuTopoUnrollSim( BasePass ):
  def __call__( s, top ):
    top.elaborate()
    GenDAGPass()( top )
    WrapGreenletPass()( top )
    HeuristicTopoPass()( top )
    UnrollTickPass()( top )
    top.lock_in_simulation()

class TraceBreakingSim( BasePass ):
  def __call__( s, top ):
    top.elaborate()
    GenDAGPass()( top )
    WrapGreenletPass()( top )
    TraceBreakingSchedTickPass()( top )
    top.lock_in_simulation()
