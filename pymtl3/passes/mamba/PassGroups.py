from ..BasePass import BasePass
from ..sim.AddSimUtilFuncsPass import AddSimUtilFuncsPass
from ..sim.GenDAGPass import GenDAGPass
from ..sim.SimpleSchedulePass import SimpleSchedulePass
from ..sim.WrapGreenletPass import WrapGreenletPass
from ..tracing.CLLineTracePass import CLLineTracePass
from ..tracing.LineTraceParamPass import LineTraceParamPass
from .HeuristicTopoPass import HeuristicTopoPass
from .Mamba2020Pass import Mamba2020Pass
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

class Mamba2020( BasePass ):
  def __init__( s, line_trace=False ):
    s.line_trace = line_trace

  def __call__( s, top ):
    top.elaborate()
    GenDAGPass()( top )
    WrapGreenletPass()( top )
    if s.line_trace:
      CLLineTracePass()( top )
      LineTraceParamPass()( top )
    Mamba2020Pass()( top )
    AddSimUtilFuncsPass()( top )
    top.lock_in_simulation()
