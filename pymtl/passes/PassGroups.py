from pymtl      import *
from simulation import GenDAGPass, SimpleSchedPass, SimpleTickPass 

#-------------------------------------------------------------------------
# SimpleSim
#-------------------------------------------------------------------------

SimpleSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  RTLComponent.lock_in_simulation
]

#-------------------------------------------------------------------------
# SimpleSchedDumpDAG
#-------------------------------------------------------------------------

def SimpleSchedDumpDAGPass():
  def currying( top ):
    return SimpleSchedPass()( top, dump_graph = True )
  return currying

SimpleSimDumpDAG = [
  RTLComponent.elaborate,
  GenDAGPass(),
  SimpleSchedDumpDAGPass(),
  SimpleTickPass(),
  RTLComponent.lock_in_simulation
]

#-------------------------------------------------------------------------
# SimpleSimNoElaboration
#-------------------------------------------------------------------------

SimpleSimNoElaboration = [
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  RTLComponent.lock_in_simulation
]

#-------------------------------------------------------------------------
# SimpleCLSim
#-------------------------------------------------------------------------

SimpleCLSim = [
  ComponentLevel6.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  ComponentLevel6.lock_in_simulation
]

#-------------------------------------------------------------------------
# UnrollSim
#-------------------------------------------------------------------------

from mamba.UnrollTickPass import UnrollTickPass
UnrollSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  UnrollTickPass(),
  RTLComponent.lock_in_simulation
]

#-------------------------------------------------------------------------
# HeuTopoUnrollSim
#-------------------------------------------------------------------------

from mamba.HeuristicTopoPass import HeuristicTopoPass
HeuTopoUnrollSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  HeuristicTopoPass(),
  UnrollTickPass(),
  RTLComponent.lock_in_simulation
]

#-------------------------------------------------------------------------
# TraceBreakingSim
#-------------------------------------------------------------------------

from mamba.TraceBreakingSchedTickPass import TraceBreakingSchedTickPass
TraceBreakingSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  TraceBreakingSchedTickPass(),
  RTLComponent.lock_in_simulation
]
