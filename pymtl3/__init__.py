from __future__ import absolute_import, division, print_function

from .datatypes import *
from .datatypes import _bitwidths
from .dsl.Component import Component
from .dsl.ComponentLevel5 import method_port
from .dsl.ComponentLevel6 import non_blocking
from .dsl.ComponentLevel7 import blocking
from .dsl.Connectable import (
    CalleePort,
    CallerPort,
    InPort,
    Interface,
    NonBlockingCalleeIfc,
    NonBlockingCallerIfc,
    OutPort,
    Wire,
)
from .dsl.ConstraintTypes import RD, WR, M, U
from .passes.PassGroups import DynamicSim, SimpleSim, SimulationPass

__version__ = "0.1.0"

__all__ = [
  'U','M','RD','WR',
  'Wire', 'InPort', 'OutPort', 'Interface', 'CallerPort', 'CalleePort',
  'method_port',
  'non_blocking', 'NonBlockingCalleeIfc', 'NonBlockingCallerIfc', 'blocking',

  'SimpleSim', 'DynamicSim', 'SimulationPass',
  'Component',

  'sext', 'zext', 'clog2', 'concat', 'reduce_and', 'reduce_or', 'reduce_xor',
  'mk_bits', 'Bits',
  'mk_bit_struct', 'BitStruct',
] + [ "Bits{}".format(x) for x in _bitwidths ] \
  + [ "b{}".format(x) for x in _bitwidths ]
