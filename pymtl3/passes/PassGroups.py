from pymtl3.dsl import Component

from .autotick.OpenLoopCLPass import OpenLoopCLPass
from .BasePass import BasePass
from .sim.DynamicSchedulePass import DynamicSchedulePass
from .sim.GenDAGPass import GenDAGPass
from .sim.SimpleSchedulePass import SimpleSchedulePass
from .sim.SimpleTickPass import SimpleTickPass
from .sim.WrapGreenletPass import WrapGreenletPass
from .tracing.CLLineTracePass import CLLineTracePass
from .tracing.CollectSignalPass import CollectSignalPass
from .tracing.LineTraceParamPass import LineTraceParamPass
from .tracing.PrintWavePass import PrintWavePass
from .tracing.VcdGenerationPass import VcdGenerationPass


# SimpleSim can be used when the UDG is a DAG
class SimpleSimPass( BasePass ):
  def __call__( s, top ):
    top.elaborate()
    GenDAGPass()( top )
    WrapGreenletPass()( top )
    SimpleSchedulePass()( top )
    CLLineTracePass()( top )
    VcdGenerationPass()( top )
    CollectSignalPass()( top )
    PrintWavePass()( top )
    SimpleTickPass()( top )
    LineTraceParamPass()( top )
    top.lock_in_simulation()

# This pass is created to be used for 2019 isca tutorial.
# Now we can always use this
class SimulationPass( BasePass ):
  def __call__( s, top ):
    top.elaborate()
    GenDAGPass()( top )
    WrapGreenletPass()( top )
    DynamicSchedulePass()( top )
    CLLineTracePass()( top )
    VcdGenerationPass()( top )
    CollectSignalPass()( top )
    PrintWavePass()( top )
    SimpleTickPass()( top )
    LineTraceParamPass()( top )
    top.lock_in_simulation()

class AutoTickSimPass( BasePass ):
  def __call__( s, top ):
    top.elaborate()
    GenDAGPass(),
    WrapGreenletPass()( top )
    OpenLoopCLPass(), # Inject this pass to build infrastructure
    top.lock_in_simulation()
