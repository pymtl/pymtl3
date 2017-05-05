from pymtl import *
from EnRdyBundle import EnRdyBundle

class DeqIfcRTL( EnRdyBundle ):
  ifc = 'Deq', 'rtl'

class DeqIfcCL( PortBundle ):
  ifc = 'Deq', 'cl'

  def __init__( s, Type ):
    s.Type = Type

    s.deq = MethodPort()
    s.rdy = MethodPort()

  def __call__( s, *args, **kwargs ):
    return s.deq( args, kwargs )

register_ifc( DeqIfcRTL )
register_ifc( DeqIfcCL )
