import os

from pymtl import *
from pymtl.passes.SystemVerilogTranslationPass import SystemVerilogTranslationPass
from pymtl.passes.SimpleImportPass import SimpleImportPass
from pymtl.passes.PassGroups import SimpleSim

def test_ImportConstraints():
  # First import the model into the sys module space
  imported = import_model( 'ImportConstraints' )

  # Then construct the test system model
  class Top( RTLComponent ):
    def construct( s ):
      s.u = Wire( Bits32 )
      s.c = Wire( Bits32 )

      from ImportConstraints_v import ImportConstraints as ImportedModel
      s.imported = ImportedModel()

      s.connect( s.imported.c, s.c )
      s.connect( s.imported.u, s.u )

      @s.update
      def a():
        s.imported.a = 10

      @s.update
      def b():
        s.imported.b = 20

      @s.update
      def c3():
        s.c = s.u + 1

    def line_trace( s ):
      return 'u={},c=u+1={}'.format( s.u, s.c ) + ' | ' + \
          s.imported.line_trace()

  # Real work here
  a = Top()
  map( lambda f: f( a ), SimpleSim )

  a.tick()
  assert a.imported.u == 30
  assert a.imported.v == 32
  print a.line_trace()

  a.tick()
  assert a.imported.u == 30
  assert a.imported.v == 32
  print a.line_trace()

def import_model( model_name, *args, **kwargs ):
  print( '\tReading PyMTL source file...' )

  py_source_file = model_name

  exec( 'import ' + model_name )
  PyMTLModel = eval( model_name + '.' + model_name )

  m = PyMTLModel( *args, **kwargs )

  print( '\tElaborating PyMTL model...' )

  m.elaborate()

  print( '\tCalling translation pass...' )

  SystemVerilogTranslationPass()( m )

  print( '\tCalling import pass...' )

  SimpleImportPass()( m )
