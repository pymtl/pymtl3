from pymtl import *
from EnRdyBundle import EnRdyBundle

class DeqIfcRTL( EnRdyBundle ):
  ifc = 'Deq'

class DeqIfcCL( PortBundle ):
  ifc = 'Deq'

  def __init__( s, Type ):
    s.Type = Type

    s.deq = MethodPort()
    s.rdy = MethodPort()

  def __call__( s, *args, **kwargs ):
    return s.deq( args, kwargs )

class DeqIfcFL( PortBundle ):
  ifc = 'Deq'

  def __init__( s, Type ):
    s.Type = Type

    s.deq = MethodPort()

# register_ifc( DeqIfcRTL, 'rtl' )
# register_ifc( DeqIfcCL,  'cl'  )
# register_ifc( DeqIfcFL,  'fl'  )
