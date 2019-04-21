from pymtl import *
from GenDAGPass import GenDAGPass
from SimpleSchedPass import SimpleSchedPass
from SimpleTickPass import SimpleTickPass

from OpenLoopCLPass import OpenLoopCLPass

SimpleSim = [
  Component.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  Component.lock_in_simulation
]

SimpleCLSim = [
  Component.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  Component.lock_in_simulation
]

OpenLoopCLSim = [
  Component.elaborate,
  GenDAGPass(),
  OpenLoopCLPass(), # Inject this pass to build infrastructure
  SimpleSchedPass(), # Still generate schedule and tick
  SimpleTickPass(),
  Component.lock_in_simulation
]

from mamba.UnrollTickPass import UnrollTickPass
UnrollSim = [
  Component.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  UnrollTickPass(),
  Component.lock_in_simulation
]

from mamba.HeuristicTopoPass import HeuristicTopoPass
HeuTopoUnrollSim = [
  Component.elaborate,
  GenDAGPass(),
  HeuristicTopoPass(),
  UnrollTickPass(),
  Component.lock_in_simulation
]

from mamba.TraceBreakingSchedTickPass import TraceBreakingSchedTickPass
TraceBreakingSim = [
  Component.elaborate,
  GenDAGPass(),
  TraceBreakingSchedTickPass(),
  Component.lock_in_simulation
]
