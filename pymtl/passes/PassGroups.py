from pymtl import *
from GenDAGPass import GenDAGPass
from SimpleSchedPass import SimpleSchedPass
from SimpleTickPass import SimpleTickPass

SimpleSim = [
  ComponentLevel6.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  ComponentLevel6.lock_in_simulation
]

SimpleCLSim = [
  ComponentLevel6.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  ComponentLevel6.lock_in_simulation
]

from mamba.UnrollTickPass import UnrollTickPass
UnrollSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  UnrollTickPass(),
  RTLComponent.lock_in_simulation
]

from mamba.HeuristicTopoPass import HeuristicTopoPass
HeuTopoUnrollSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  HeuristicTopoPass(),
  UnrollTickPass(),
  RTLComponent.lock_in_simulation
]

from mamba.TraceBreakingSchedTickPass import TraceBreakingSchedTickPass
TraceBreakingSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  TraceBreakingSchedTickPass(),
  RTLComponent.lock_in_simulation
]
