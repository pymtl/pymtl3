from __future__ import absolute_import, division, print_function

from pymtl3.dsl import Component

from .CLLineTracePass import CLLineTracePass
from .DynamicSchedulePass import DynamicSchedulePass
from .GenDAGPass import GenDAGPass
from .mamba.HeuristicTopoPass import HeuristicTopoPass
from .mamba.TraceBreakingSchedTickPass import TraceBreakingSchedTickPass
from .mamba.UnrollTickPass import UnrollTickPass
from .OpenLoopCLPass import OpenLoopCLPass
from .SimpleSchedulePass import SimpleSchedulePass
from .SimpleTickPass import SimpleTickPass
from .VcdGenerationPass import VcdGenerationPass
from .WrapGreenletPass import WrapGreenletPass

SimpleSim = [
  Component.elaborate,
  GenDAGPass(),
  WrapGreenletPass(),
  SimpleSchedulePass(),
  CLLineTracePass(),
  SimpleTickPass(),
  Component.lock_in_simulation
]

DynamicSim = [
  Component.elaborate,
  GenDAGPass(),
  WrapGreenletPass(),
  DynamicSchedulePass(),
  CLLineTracePass(),
  SimpleTickPass(),
  Component.lock_in_simulation
]

OpenLoopCLSim = [
  Component.elaborate,
  GenDAGPass(),
  OpenLoopCLPass(), # Inject this pass to build infrastructure
  SimpleSchedulePass(), # Still generate schedule and tick
  # TODO: make OpenLoopCLPass work with CLLineTracePass
  SimpleTickPass(),
  Component.lock_in_simulation
]

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
