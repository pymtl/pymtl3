#========================================================================
# UniqueModule.py
#========================================================================
# This module includes a test case to check whether the translation pass
# can avoid translating duplicated modules in the model hierarchy. 

from pymtl import *

class DeepModule( RTLComponent ):

  def construct( s ):

    s.in_ = InVPort ( Bits8 )
    s.out = OutVPort( Bits8 )

    @s.update
    def deep_block():
      s.out = Bits8( 0xff )

class Foo( RTLComponent ):

  def construct( s ):

    s.in_ = InVPort ( Bits16 )
    s.out = OutVPort( Bits16 )

    s.deep_mod = DeepModule()

    @s.update
    def foo_block(): 
      s.out = Bits16( 0xffff )

class Bar( RTLComponent ):

  def construct( s ):

    s.in_ = InVPort ( Bits16 )
    s.out = OutVPort( Bits16 )

    s.deep_mod = DeepModule()

    @s.update
    def foo_block(): 
      s.out = Bits16( 0xffff )

class UniqueModule( RTLComponent ):

  def construct( s ):
    s.in_  = InVPort ( Bits16 )
    s.out1 = OutVPort( Bits16 )
    s.out2 = OutVPort( Bits16 )

    s.foo = Foo()

    s.connect( s.foo.in_, s.in_ )
    s.connect( s.foo.out, s.out1 )

    s.bar = Bar()

    s.connect( s.bar.in_, s.in_ )
    s.connect( s.bar.out, s.out2 )

