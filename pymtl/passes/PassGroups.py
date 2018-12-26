from pymtl import *
from GenDAGPass import GenDAGPass
from SimpleSchedTickPass import SimpleSchedTickPass

SimpleSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  SimpleSchedTickPass(),
  RTLComponent.lock_in_simulation
]
