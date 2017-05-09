from pymtl import *
from EnqIfcs import EnqIfcCL, EnqIfcRTL

class MemIfcFL( PortBundle ):
  ifc = 'Mem'

  def __init__( s ):
    s.read  = MethodPort()
    s.write = MethodPort()
    s.amo   = MethodPort()

class MemIfcCL( PortBundle ):
  ifc = 'Mem'

  def __init__( s, Type1, Type2 ):
    s.Type = Type1, Type2

    s.req  = EnqIfcCL( Type1 )
    s.resp = EnqIfcCL( Type2 )

  def __call__( s, *args, **kwargs ):
    return s.enq( args, kwargs )

class MemIfcRTL( PortBundle ):
  ifc = 'Mem'

  def __init__( s, Type1, Type2 ):
    s.Type = Type1, Type2

    s.req  = EnqIfcRTL( Type1 )
    s.resp = EnqIfcRTL( Type2 )

register_ifc( MemIfcFL,  'fl'  )
register_ifc( MemIfcCL,  'cl'  )
register_ifc( MemIfcRTL, 'rtl' )
