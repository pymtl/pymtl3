from ..BasePass import BasePass
from ..sim.PrepareSimPass import PrepareSimPass
from ..sim.GenDAGPass import GenDAGPass
from ..sim.SimpleSchedulePass import SimpleSchedulePass
from ..sim.WrapGreenletPass import WrapGreenletPass
from ..tracing.CLLineTracePass import CLLineTracePass
from ..tracing.LineTraceParamPass import LineTraceParamPass
from .HeuristicTopoPass import HeuristicTopoPass
from .Mamba2020Pass import Mamba2020Pass
from .TraceBreakingSchedTickPass import TraceBreakingSchedTickPass
from .UnrollSimPass import UnrollSimPass


class UnrollSim( BasePass ):
  def __init__( s, *, waveform=None, print_line_trace=True, reset_active_high=True ):
    s.waveform = waveform
    s.print_line_trace = print_line_trace
    s.reset_active_high = reset_active_high

  def __call__( s, top ):
    top.elaborate()
    GenDAGPass()( top )
    WrapGreenletPass()( top )
    SimpleSchedulePass()( top )
    UnrollSimPass()( top )

class HeuTopoUnrollSim( BasePass ):
  def __call__( s, top ):
    top.elaborate()
    GenDAGPass()( top )
    WrapGreenletPass()( top )
    HeuristicTopoPass()( top )
    PrepareSimPass()( top )

class TraceBreakingSim( BasePass ):
  def __call__( s, top ):
    top.elaborate()
    GenDAGPass()( top )
    WrapGreenletPass()( top )
    TraceBreakingSchedTickPass()( top )
    PrepareSimPass()( top )

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
