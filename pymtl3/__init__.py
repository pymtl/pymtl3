from .datatypes import *
from .datatypes import _bitwidths
from .dsl import *
from .passes.PassGroups import SimulationPass
from .passes.backends.sverilog import TranslationImportPass, ImportPass
from .passes import TracingConfigs, ImportConfigs

__version__ = "0.5.4"

__all__ = [
  'U','M','RD','WR',
  'Wire', 'InPort', 'OutPort', 'Interface', 'CallerPort', 'CalleePort',
  'connect', 'method_port',
  'non_blocking', 'NonBlockingCalleeIfc', 'NonBlockingCallerIfc', 'blocking',

  'SimulationPass', 'TracingConfigs', 'TranslationImportPass', 'ImportPass',
  'Component', 'Placeholder',

  'sext', 'zext', 'clog2', 'concat', 'reduce_and', 'reduce_or', 'reduce_xor',
  'mk_bits', 'Bits',
  'mk_bitstruct', 'bitstruct',
  'to_bits', 'get_nbits',
] + [ "Bits{}".format(x) for x in _bitwidths ] \
  + [ "b{}".format(x) for x in _bitwidths ]
