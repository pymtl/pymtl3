from pymtl import *
from GenDAGPass import GenDAGPass
from SimpleSchedPass import SimpleSchedPass
from SimpleTickPass import SimpleTickPass
from mamba.UnrollTickPass import UnrollTickPass
from mamba.HeuristicTopoPass import HeuristicTopoPass

SimpleSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  RTLComponent.lock_in_simulation
]

UnrollSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  UnrollTickPass(),
  RTLComponent.lock_in_simulation
]

HeuTopoUnrollSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  HeuristicTopoPass(),
  UnrollTickPass(),
  RTLComponent.lock_in_simulation
]

#  HeuTopoTraceBreakSim = [
  #  RTLComponent.elaborate,
  #  GenDAGPass(),
  #  SimpleSchedPass(),
  #  UnrollTickPass(),
  #  RTLComponent.lock_in_simulation
#  ]
