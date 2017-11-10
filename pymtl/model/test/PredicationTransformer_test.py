from pymtl import *
from pymtl.model import PredicationTransformer
import ast

def predicate_and_check( in_src, exp_src ):
  in_ = ast.parse( in_src ).body[0]
  out = PredicationTransformer().visit( in_ )
  exp = ast.parse( exp_src ).body[0]
  assert ast.dump( out ) == ast.dump( exp )

def test_if():
  predicate_and_check( """
def foo1( s ):
  if a:
    s.b = 1
        """, """
def foo1( s ):
  s.b = [ s.b, 1 ][ a == True ]
""" )

def test_ifelse():
  predicate_and_check( """
def foo1( s ):
  if a:
    s.b = 1
  else:
    s.b = 2
        """, """
def foo1( s ):
  s.b = [ 2, 1 ][ a == True ]
""" )

def test_ifelse_multistmt():
  predicate_and_check( """
def foo1( s ):
  if a:
    s.b = 1
    s.c = 3
  else:
    s.b = 2
    s.c = 4
        """, """
def foo1( s ):
  s.b = [ 2, 1 ][ a == True ]
  s.c = [ 4, 3 ][ a == True ]
""" )

def test_ifelif():
  predicate_and_check( """
def foo1( s ):
  if a:
    s.b = 1
  elif b:
    s.b = 3
  else:
    s.b = 2
        """, """
def foo1( s ):
  s.b = [ [2, 3][ b == True], 1 ][ a == True ]
""" )

def test_else():
  predicate_and_check( """
def foo1( s ):
  if a:
    pass
  else:
    s.b = 2
        """, """
def foo1( s ):
  s.b = [ 2, s.b ][ a == True ]
""" )

def test_if_default():
  predicate_and_check( """
def foo1( s ):
  s.b = 0
  if a:
    s.b = 1
        """, """
def foo1( s ):
  s.b = 0
  s.b = [ s.b, 1 ][ a == True ]
""" )

def test_if_nested():
  predicate_and_check( """
def foo1( s ):
  if a:
    if c:
      s.b = 1
        """, """
def foo1( s ):
  s.b = [ s.b, [ s.b, 1 ][ c == True ] ][ a == True ]
""" )

def test_if_nested_fail():
  predicate_and_check( """
def foo1( s ):
  if a:
    s.b = 0
    if c:
      s.b = 1
        """, """
def foo1( s ):
  if a:
    s.b = 0
    if c:
      s.b = 1
""" )

def test_ifelse_fail():
  predicate_and_check( """
def foo1( s ):
  if a:
    s.b = 1
  else:
    s.b = 2
    foo2()
        """, """
def foo1( s ):
  if a:
    s.b = 1
  else:
    s.b = 2
    foo2()
""" )


def test_if_nested2():
  predicate_and_check( """
def foo1( s ):
  if a:
    if c:
      s.b = 1
  elif b:
    if d:
      s.a = 2
    else:
      s.b = 5
  else:
    s.b = 2
        """, """
def foo1( s ):
  s.b = [ [2, [5, s.b][ d == True ] ][ b == True ],
          [s.b, 1][ c == True ] ][ a == True ]
  s.a = [ [s.a, [s.a, 2][ d == True ] ][ b == True ],
          s.a ][ a == True ]
""" )
