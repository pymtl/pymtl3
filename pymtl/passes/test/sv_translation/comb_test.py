from pymtl import *
from pclib.rtl import Adder, Mux
from pymtl.passes.SVTranslationPass import SVTranslationPass

def test_adder():
  m = Adder( Bits32 )
  SVTranslationPass().apply( m )
  
def test_multiple_if():

  class Foo( UpdateVarNet ):
    def __init__( s ):
      s.in_  = InVPort( Bits2 )
      s.out  = OutVPort( Bits2 )

      @s.update
      def up_if():
        if   s.in_ == ~s.in_:         s.out = s.in_
        elif s.in_ == s.in_ & s.in_:  s.out = ~s.in_
        elif s.in_ == s.in_ | s.in_:
          s.out = s.in_
          s.out = s.in_
          s.out = s.in_
        else:                         s.out = s.in_ + s.in_

  m = Foo()
  SVTranslationPass().apply( m )

def test_bits_type():

  class Foo( UpdateVarNet ):
    def __init__( s ):
      s.in_  = InVPort( Bits2 )
      s.out  = OutVPort( Bits4 )

      @s.update
      def up_if():
        if   s.in_ == Bits2( 0 ):
          s.out = Bits4( 1 ) | Bits4( 2 )
          s.out = Bits4( 8 )
        else:
          s.out = Bits1( 0 )
          s.out = Bits4( 1 )

  m = Foo()
  SVTranslationPass().apply( m )

def test_bits_type_in_self():

  class Foo( UpdateVarNet ):
    def __init__( s ):
      nbits = 2

      s.Tin  = mk_bits( nbits )
      s.in_  = InVPort( s.Tin )
      s.Tout = mk_bits( 1<<nbits )
      s.out  = OutVPort( s.Tout )

      @s.update
      def up_if():
        if   s.in_ == Bits123( 0 ):
          s.out = s.Tout( 1 ) | s.Tout( 1 )
          s.out = s.Tout( 8 )
        else:
          s.out = s.Tout( 0 )

  m = Foo()
  SVTranslationPass().apply( m )

def test_bits_val_and_call():

  class Foo( UpdateVarNet ):
    def __init__( s ):
      nbits = 2

      s.Tin  = mk_bits( nbits )
      s.in_  = InVPort( s.Tin )
      s.Tout = mk_bits( 1<<nbits )
      s.out  = OutVPort( s.Tout )


      @s.func
      def qnm( x ):
        s.out = x

      @s.update
      def up_if():

        if   s.in_ == s.Tin( 0 ):
          s.out = s.Tout( 1 ) | s.Tout( 1 )

        elif s.in_ == s.Tin( 1 ):
          s.out = s.Tout( 2 ) & s.Tout( 2 )
          s.out = ~s.Tout( 2 )

        elif s.in_ == s.Tin( 2 ):
          s.out = s.Tout( 4 ) < s.Tout( 3 )
          s.out = s.Tout( 4 ) if s.in_ == s.Tin( 2 ) else s.Tout( 5 )
  
        elif s.in_ == s.Tin( 3 ):
          s.out = s.Tout( 8 )

        else:
          s.out = s.Tout( 0 )
          qnm( s.Tout( 0 ) )

  m = Foo()
  SVTranslationPass().apply( m )
