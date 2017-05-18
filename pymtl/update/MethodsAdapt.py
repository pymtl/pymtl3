#=========================================================================
# MethodsAdapt.py
#=========================================================================
# At this level, we add the ability to automatically inject adapter

from MethodsConnection import MethodsConnection
from collections import defaultdict
from Connectable import PortBundle

#{ ifc1:{ level1:type1, level2:type2, ... }, ifc2:{..}, .. }

ifc_registry     = defaultdict(dict)
adapter_registry = defaultdict(dict)

# used to make sure one name corresponds to one base type
def register_ifc( ifc, level ):
  assert hasattr( ifc, "ifc" ), "Interface %s should define class variable 'ifc = name, level'" % ifc.__name__

  type_     = ifc.ifc
  ifc._level = level

  ifc_levels = ifc_registry[ type_ ]
  assert level not in ifc_levels, "Cannot register two types with the same level '%s' for interface '%s': %s(previous), %s(new)" \
                                    % (level, type_, ifc_levels[level].__name__, ifc.__name__)
  ifc_levels[ level ] = ifc

def register_adapter( adapter, xlevel, ylevel ):
  assert hasattr( adapter, "ifcs" ), "Adapter %s should define class variable 'ifcs = name1, name2'" % adapter.__name__
  xname,  yname = adapter.ifcs

  assert hasattr( adapter, "types" ), "Adapter %s should define class variable 'types = type1, type1'" % adapter.__name__
  xtype,  ytype = adapter.types

  adapter_levels = adapter_registry[ (xtype, ytype) ]

  assert (xlevel, ylevel) not in adapter_levels, "Cannot register two adapters for the same pair of interfaces <%s_%s - %s_%s>: %s(previous), %s(new)" \
                                    % (xtype, xlevel, ytype, ylevel, adapter_levels[ (xlevel, ylevel) ].__name__, adapter.__name__)
  adapter_levels[ (xlevel, ylevel) ] = adapter

class MethodsAdapt( MethodsConnection ):

  # Override
  def __new__( cls, *args, **kwargs ):
    inst = super( MethodsAdapt, cls ).__new__( cls, *args, **kwargs )
    return inst

  def pausable_update( s, blk ):
    blk._pausable = True
    s.update( blk )
    return blk

  def connect( s, x, y ):
    if not isinstance( x, PortBundle ) or not isinstance( x, PortBundle ):
      x |= y
      return

    # The interface(portbundle) will provide its type and level

    xtype  = x.ifc
    ytype  = y.ifc

    # Check if x's and y's type are registered, and if x's and y's type matches the registered type

    assert xtype in ifc_registry and hasattr( x, "_level" ), "Interface type %s is not registered at all." % type(x).__name__
    xlevel = x._level
    assert xlevel in ifc_registry[xtype], "Level '%s' of interface type %s is not registered." % (xlevel, type(x).__name__)
    assert isinstance( x, ifc_registry[xtype][xlevel] ), "The left hand side is called '%s' but is of type '%s', not the registered type '%s'" % (xname, type(x).__name__, xclass.__name__,)

    assert ytype in ifc_registry and hasattr( y, "_level" ), "Interface type %s is not registered at all." % type(y).__name__
    ylevel = y._level
    assert ylevel in ifc_registry[ytype], "Level '%s' of interface type %s is not registered." % (ylevel, type(y).__name__)
    assert isinstance( y, ifc_registry[ytype][ylevel] ), "The right hand side is called '%s' but is of type '%s', not the registered type '%s'" % (yname, type(y).__name__ , yclass.__name__)

    # Check if they are the same interface

    if xlevel == ylevel and xtype == ytype and type(x) == type(y):
      if x.Type == y.Type:
        x |= y
        return
      else:
        print "Warning: ",x.Type.__dict__,y.Type.__dict__

    # Generating a unique name. Lookup the type registry to construct adapter.

    if not hasattr( s, "_num_adapters" ): s._num_adapters = 0
    else: s._num_adapters += 1
    adapter      = adapter_registry[ (xtype, ytype) ][ (xlevel, ylevel) ](x.Type, xlevel, y.Type, ylevel)
    adapter_name = "{}_{}_{}_{}_{}".format( xtype, xlevel, ytype, ylevel, s._num_adapters )

    assert not hasattr( s, adapter_name )
    setattr( s, adapter_name, adapter )

    # Connect the corresponding ports to adapter interfaces

    x |= getattr( adapter, adapter.ifcs[0] )
    y |= getattr( adapter, adapter.ifcs[1] )

    print "Generating an adapter {}({}) <--> {}({}) using {}".format( xtype, xlevel, ytype, ylevel, type(adapter).__name__ )

  # Override
  def _generate_tick_func( s ):
    import greenlet
    import py.code

    schedule = s._schedule_list
    tmp_list = []
    nblks = len(schedule)

    for i in xrange(nblks):
      if hasattr( schedule[i], "_pausable" ):
        greenlet_wrap_src = py.code.Source("""
          blk{0} = schedule[{0}]

          def loop_wrap{0}():
            while True:
              blk{0}()
              greenlet.greenlet.getcurrent().parent.switch()

          greenlet{0} = greenlet.greenlet( loop_wrap{0} )

          def {1}_GREENLET():
            greenlet{0}.switch()

          tmp_list.append( {1}_GREENLET )
        """.format(i, schedule[i].__name__) )

        exec greenlet_wrap_src.compile() in locals()

      else:
        tmp_list.append( schedule[i] )

    s._schedule_list = tmp_list

    super( MethodsAdapt, s )._generate_tick_func()
