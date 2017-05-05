from pymtl import *
from EnRdyBundle import EnRdyBundle

class EnqIfcRTL( EnRdyBundle ):
  ifc = 'Enq'

class EnqIfcCL( PortBundle ):
  ifc = 'Enq'

  def __init__( s, Type ):
    s.Type = Type

    s.enq = MethodPort()
    s.rdy = MethodPort()

  def __call__( s, *args, **kwargs ):
    return s.enq( args, kwargs )

register_ifc( EnqIfcRTL, 'rtl' )
register_ifc( EnqIfcCL,  'cl'  )
