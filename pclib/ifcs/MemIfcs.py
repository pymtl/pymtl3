from pymtl import *
from EnqIfcs import EnqIfcCL, EnqIfcRTL

class MemIfcFL( PortBundle ):
  ifc = 'Mem'

  def __init__( s ):
    s.Type  = None
    s.read  = MethodPort()
    s.write = MethodPort()
    s.amo   = MethodPort()

class MemIfcCL( PortBundle ):
  ifc = 'Mem'

  def __init__( s, Type ):
    assert len(Type) == 2
    s.Type = Type

    s.req  = EnqIfcCL( Type[0] )
    s.resp = EnqIfcCL( Type[1] )

  def __call__( s, *args, **kwargs ):
    return s.enq( args, kwargs )

class MemIfcRTL( PortBundle ):
  ifc = 'Mem'

  def __init__( s, Type ):
    assert len(Type) == 2
    s.Type = Type

    s.req  = EnqIfcRTL( Type[0] )
    s.resp = EnqIfcRTL( Type[1] )

# register_ifc( MemIfcFL,  'fl'  )
# register_ifc( MemIfcCL,  'cl'  )
# register_ifc( MemIfcRTL, 'rtl' )
