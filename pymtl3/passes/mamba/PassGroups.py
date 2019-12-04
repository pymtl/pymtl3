from .HeuristicTopoPass import HeuristicTopoPass
from .TraceBreakingSchedTickPass import TraceBreakingSchedTickPass
from .UnrollTickPass import UnrollTickPass

UnrollSim = [
  Component.elaborate,
  GenDAGPass(),
  WrapGreenletPass(),
  SimpleSchedulePass(),
  UnrollTickPass(),
  Component.lock_in_simulation
]

HeuTopoUnrollSim = [
  Component.elaborate,
  GenDAGPass(),
  HeuristicTopoPass(),
  UnrollTickPass(),
  Component.lock_in_simulation
]

TraceBreakingSim = [
  Component.elaborate,
  GenDAGPass(),
  TraceBreakingSchedTickPass(),
  Component.lock_in_simulation
]
