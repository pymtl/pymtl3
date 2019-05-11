from __future__ import absolute_import, division, print_function

from pymtl import *

from .DynamicSchedulePass import DynamicSchedulePass
from .GenDAGPass import GenDAGPass
from .mamba.HeuristicTopoPass import HeuristicTopoPass
from .mamba.TraceBreakingSchedTickPass import TraceBreakingSchedTickPass
from .mamba.UnrollTickPass import UnrollTickPass
from .SimpleSchedulePass import SimpleSchedulePass
from .SimpleTickPass import SimpleTickPass

SimpleSim = [
  Component.elaborate,
  GenDAGPass(),
  SimpleSchedulePass(),
  SimpleTickPass(),
  Component.lock_in_simulation
]

DynamicSim = [
  Component.elaborate,
  GenDAGPass(),
  DynamicSchedulePass(),
  SimpleTickPass(),
  Component.lock_in_simulation
]

SimpleCLSim = [
  Component.elaborate,
  GenDAGPass(),
  SimpleSchedulePass(),
  SimpleTickPass(),
  Component.lock_in_simulation
]

UnrollSim = [
  Component.elaborate,
  GenDAGPass(),
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
