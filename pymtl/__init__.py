
from components.ConstraintTypes import U, M, RD, WR
from components.Connectable     import Wire, InVPort, OutVPort, Interface
from components.UpdateVarNet    import UpdateVarNet

from datatypes import *
from datatypes import _bitwidths

# from passes import SimUpdateVarNetPass

__all__ = [
  'U','M','RD','WR',
  'Wire', 'InVPort', 'OutVPort', 'Interface',

  'UpdateVarNet',# 'SimUpdateVarNetPass',

  'sext', 'zext', 'clog2', 'concat',
  'mk_bits', 'Bits'
] + [ "Bits{}".format(x) for x in _bitwidths ]
