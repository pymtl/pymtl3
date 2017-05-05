#=========================================================================
# MethodsAdapt.py
#=========================================================================
# At this level, we add the ability to automatically inject adapter

from MethodsConnection import MethodsConnection
from Connectable import MethodPort
from collections import defaultdict

#{ ifc1:{ level1:type1, level2:type2, ... }, ifc2:{..}, .. }

ifc_registry     = defaultdict(dict)
adapter_registry = defaultdict(dict)

# used to make sure one name corresponds to one base type
def register_ifc( ifc ):
  assert hasattr( ifc, "ifc" ), "Interface %s should define class variable 'ifc = name, level'" % ifc.__name__

  type_, level = ifc.ifc
  ifc_levels  = ifc_registry[ type_ ]
  assert level not in ifc_levels, "Cannot register two types with the same level '%s' for interface '%s': %s(previous), %s(new)" \
                                    % (level, type_, ifc_levels[level].__name__, ifc.__name__)
  ifc_levels[ level ] = ifc

def register_adapter( adapter ):
  assert hasattr( adapter, "ifcs" ), "Adapter %s should define class variable 'ifcs = name1, name2'" % adapter.__name__
  xname,  yname = adapter.ifcs

  assert hasattr( adapter, "types" ), "Adapter %s should define class variable 'types = type1, type1'" % adapter.__name__
  xtype,  ytype = adapter.types

  assert hasattr( adapter, "levels" ), "Adapter %s should define class variable 'levels = level1, level2'" % adapter.__name__
  xlevel, ylevel = adapter.levels

  adapter_levels = adapter_registry[ (xtype, ytype) ]

  assert (xlevel, ylevel) not in adapter_levels, "Cannot register two adapters for the same pair of interfaces <%s_%s - %s_%s>: %s(previous), %s(new)" \
                                    % (xtype, xlevel, ytype, ylevel, adapter_levels[ (xlevel, ylevel) ].__name__, adapter.__name__)
  print xtype, ytype, xlevel, ylevel
  adapter_levels[ (xlevel, ylevel) ] = adapter

class MethodsAdapt( MethodsConnection ):

  # Override
  def __new__( cls, *args, **kwargs ):
    inst = super( MethodsAdapt, cls ).__new__( cls, *args, **kwargs )
    return inst

  def connect_ifcs( s, x, y ):

    # The interface(portbundle) will provide its type and level

    xtype, xlevel = x.ifc
    ytype, ylevel = y.ifc

    # Check if x's and y's type are registered

    assert xtype in ifc_registry, "Interface type %s is not registered at all." % type(x).__name__
    assert xlevel in ifc_registry[ytype], "Level '%s' of interface type %s is not registered." % (xlevel, type(x).__name__)
    assert ytype in ifc_registry, "Interface type %s is not registered at all." % type(y).__name__
    assert ylevel in ifc_registry[ytype], "Level '%s' of interface type %s is not registered." % (ylevel, type(y).__name__)

    # Check if x's and y's type matches the registered type

    assert isinstance( x, ifc_registry[xtype][xlevel] ), "The left hand side is called '%s' but is of type '%s', not the registered type '%s'" % (xname, type(x).__name__, xclass.__name__,)
    assert isinstance( y, ifc_registry[ytype][ylevel] ), "The right hand side is called '%s' but is of type '%s', not the registered type '%s'" % (yname, type(y).__name__ , yclass.__name__)

    # Generating a name with id

    if not hasattr( s, "_num_adapters" ): s._num_adapters = 0
    else: s._num_adapters += 1

    # Generate this adapter by looking up the adapter type

    adapter      = adapter_registry[ (xtype, ytype) ][ (xlevel, ylevel) ](x.Type, y.Type)
    adapter_name = "{}_{}_{}_{}_{}".format( xtype, xlevel, ytype, ylevel, s._num_adapters )

    assert not hasattr( s, adapter_name )
    setattr( s, adapter_name, adapter )

    # Connect the corresponding ports to adapter interfaces

    x |= getattr( adapter, adapter.ifcs[0] )
    y |= getattr( adapter, adapter.ifcs[1] )

    print "Generating an adapter {}({}) <--> {}({}) using {}".format( xtype, xlevel, ytype, ylevel, type(adapter).__name__ )
