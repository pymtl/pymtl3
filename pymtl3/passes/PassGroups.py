from .autotick.OpenLoopCLPass import OpenLoopCLPass
from .BasePass import BasePass
from .linting.CheckSignalNamePass import CheckSignalNamePass
from .linting.CheckUnusedSignalPass import CheckUnusedSignalPass
from .sim.DynamicSchedulePass import DynamicSchedulePass
from .sim.GenUDGPass import GenUDGPass
from .sim.PrepareSimPass import PrepareSimPass
from .sim.SimpleSchedulePass import SimpleSchedulePass
from .sim.SimpleTickPass import SimpleTickPass
from .sim.WrapGreenletPass import WrapGreenletPass
from .stats.DumpUDGPass import DumpUDGPass
from .tracing.CLLineTracePass import CLLineTracePass
from .tracing.LineTraceParamPass import LineTraceParamPass
from .tracing.PrintTextWavePass import PrintTextWavePass
from .tracing.VcdGenerationPass import VcdGenerationPass


# SimpleSim can be used when the UDG is a DAG
class SimpleSimPass( BasePass ):
  def __call__( s, top ):
    LineTraceParamPass()( top )
    GenUDGPass()( top )
    WrapGreenletPass()( top )
    SimpleSchedulePass()( top )
    CLLineTracePass()( top )
    VcdGenerationPass()( top )
    PrintTextWavePass()( top )

    PrepareSimPass(print_line_trace=True)( top )

class DefaultPassGroup( BasePass ):
  def __init__( s, *, dump_udg=False, linting=False, vcdwave=None, textwave=False,
                      print_line_trace=True, reset_active_high=True ):

    s.dump_udg = dump_udg
    s.linting = linting
    s.vcdwave = vcdwave
    s.textwave = textwave
    s.print_line_trace = print_line_trace
    s.reset_active_high = reset_active_high

  def __call__( s, top ):

    if s.linting:
      CheckSignalNamePass()( top )
      CheckUnusedSignalPass()( top )

    if s.vcdwave:
      top.set_metadata( VcdGenerationPass.vcdwave, s.vcdwave )

    if s.textwave:
      top.set_metadata( PrintTextWavePass.enable, True )

    GenUDGPass()( top )

    if s.dump_udg:
      DumpUDGPass()( top )

    WrapGreenletPass()( top )
    CLLineTracePass()( top )
    LineTraceParamPass()( top )
    DynamicSchedulePass()( top )
    VcdGenerationPass()( top )
    PrintTextWavePass()( top )

    PrepareSimPass(print_line_trace=s.print_line_trace,
                   reset_active_high=s.reset_active_high)( top )

class AutoTickSimPass( BasePass ):
  def __init__( s, print_line_trace=True ):
    s.print_line_trace = print_line_trace

  def __call__( s, top ):
    top.elaborate()
    GenUDGPass()( top )
    WrapGreenletPass()( top )
    OpenLoopCLPass( s.print_line_trace )( top )
    top.lock_in_simulation()
