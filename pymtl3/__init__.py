from .datatypes import *
from .datatypes import _bitwidths
from .dsl.Component import Component
from .dsl.ComponentLevel3 import connect
from .dsl.ComponentLevel5 import method_port
from .dsl.ComponentLevel6 import non_blocking
from .dsl.ComponentLevel7 import blocking
from .dsl.Connectable import (
    CalleeIfcCL,
    CalleeIfcFL,
    CalleeIfcRTL,
    CalleePort,
    CallerIfcCL,
    CallerIfcFL,
    CallerIfcRTL,
    CallerPort,
    InPort,
    Interface,
    OutPort,
    Wire,
)
from .dsl.ConstraintTypes import RD, WR, M, U
from .dsl.Placeholder import Placeholder
from .passes import ImportConfigs, TracingConfigs
from .passes.backends.sverilog import ImportPass, TranslationImportPass
from .passes.PassGroups import SimulationPass

__version__ = "0.5.5"

__all__ = [
  'U','M','RD','WR',
  'Wire', 'InPort', 'OutPort', 'Interface', 'CallerPort', 'CalleePort',
  'connect', 'method_port',
  'CalleeIfcRTL', 'CallerIfcRTL',
  'non_blocking', 'CalleeIfcCL', 'CallerIfcCL',
  'blocking', 'CalleeIfcFL', 'CallerIfcFL',

  'SimulationPass', 'TracingConfigs', 'TranslationImportPass', 'ImportPass',
  'Component', 'Placeholder',

  'sext', 'zext', 'clog2', 'concat', 'reduce_and', 'reduce_or', 'reduce_xor',
  'mk_bits', 'Bits',
  'mk_bitstruct', 'bitstruct',
  'to_bits', 'get_nbits',
] + [ "Bits{}".format(x) for x in _bitwidths ] \
  + [ "b{}".format(x) for x in _bitwidths ]
