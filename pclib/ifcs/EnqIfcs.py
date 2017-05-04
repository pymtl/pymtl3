from pymtl import *
from EnRdyBundle import EnRdyBundle

class EnqIfcRTL( EnRdyBundle ):
  ifc_name  = 'Enq'
  ifc_level = 'rtl'

class EnqIfcCL( PortBundle ):
  ifc_name  = 'Enq'
  ifc_level = 'cl'

  def __init__( s, Type ):
    s.Type = Type

    s.enq = MethodPort()
    s.rdy = MethodPort()

  def __call__( s, *args, **kwargs ):
    return s.enq( args, kwargs )
