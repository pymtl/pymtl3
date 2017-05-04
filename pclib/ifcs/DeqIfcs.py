from pymtl import *
from EnRdyBundle import EnRdyBundle

class DeqIfcRTL( EnRdyBundle ):
  ifc_name  = 'Enq'
  ifc_level = 'rtl'

class DeqIfcCL( PortBundle ):
  ifc_name  = 'Enq'
  ifc_level = 'cl'

  def __init__( s, Type ):
    s.Type = Type

    s.deq = MethodPort()
    s.rdy = MethodPort()

  def __call__( s, *args, **kwargs ):
    return s.deq( args, kwargs )
