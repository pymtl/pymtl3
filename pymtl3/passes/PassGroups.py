from pymtl3.dsl import Component

from .CLLineTracePass import CLLineTracePass
from .DynamicSchedulePass import DynamicSchedulePass
from .GenDAGPass import GenDAGPass
from .LineTraceParamPass import LineTraceParamPass
from .mamba.HeuristicTopoPass import HeuristicTopoPass
from .mamba.TraceBreakingSchedTickPass import TraceBreakingSchedTickPass
from .mamba.UnrollTickPass import UnrollTickPass
from .OpenLoopCLPass import OpenLoopCLPass
from .SimpleSchedulePass import SimpleSchedulePass
from .SimpleTickPass import SimpleTickPass
from .text_wave.CollectSignalPass import CollectSignalPass
from .text_wave.PrintWavePass import PrintWavePass
from .VcdGenerationPass import VcdGenerationPass
from .WrapGreenletPass import WrapGreenletPass

SimpleSim = [
  Component.elaborate,
  GenDAGPass(),
  WrapGreenletPass(),
  CLLineTracePass(),
  SimpleSchedulePass(),
  # VcdGenerationPass(),
  CollectSignalPass(),
  PrintWavePass(),
  SimpleTickPass(),
  LineTraceParamPass(),
  Component.lock_in_simulation
]

DynamicSim = [
  Component.elaborate,
  GenDAGPass(),
  WrapGreenletPass(),
  CLLineTracePass(),
  DynamicSchedulePass(),
  CLLineTracePass(),
  SimpleTickPass(),
  Component.lock_in_simulation
]

# This pass is created to be used for 2019 isca tutorial.
SimulationPass = [
  GenDAGPass(),
  WrapGreenletPass(),
  CLLineTracePass(),
  DynamicSchedulePass(),
  VcdGenerationPass(),
  CollectSignalPass(),
  PrintWavePass(),
  SimpleTickPass(),
  Component.lock_in_simulation
]

OpenLoopCLSim = [
  Component.elaborate,
  GenDAGPass(),
  WrapGreenletPass(),
  CLLineTracePass(),
  OpenLoopCLPass(), # Inject this pass to build infrastructure
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
