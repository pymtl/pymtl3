#=========================================================================
# NamedObject_test.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Dec 23, 2017

from pymtl import *
from pymtl.dsl import NamedObject
from collections import deque

class Chicken(NamedObject):

  def construct( s ):
    s.protein = NamedObject()

class Dog(NamedObject):

  def construct( s ):
    s.chicken = Chicken()

class Tiger(NamedObject):

  def construct( s ):
    s.rooster = Chicken()

class Human(NamedObject):

  def construct( s, nlunch=1, ndinner=1 ):

    if nlunch == 1: s.lunch = Tiger()
    else:           s.lunch = [ Tiger() for _ in xrange(nlunch) ]

    if ndinner == 1: s.dinner = Dog()
    else:            s.dinner = [ Dog() for _ in xrange(ndinner) ]

def test_NamedObject_normal():

  x = Human( nlunch=1, ndinner=1 )
  x.elaborate()

  assert repr(x) == "s"

  assert repr(x.lunch) == "s.lunch"
  assert repr(x.dinner) == "s.dinner"

  assert repr(x.lunch.rooster) == "s.lunch.rooster"
  assert repr(x.dinner.chicken)== "s.dinner.chicken"

  assert repr(x.lunch.rooster.protein) == "s.lunch.rooster.protein"
  assert repr(x.dinner.chicken.protein)== "s.dinner.chicken.protein"
  print x.dinner.chicken.protein

def test_NamedObject_list1():

  x = Human( nlunch=1, ndinner=5 )
  x.elaborate()

  assert repr(x) == "s"

  assert repr(x.lunch) == "s.lunch"
  assert repr(x.dinner[2]) == "s.dinner[2]"

  assert repr(x.lunch.rooster) == "s.lunch.rooster"
  assert repr(x.dinner[2].chicken)== "s.dinner[2].chicken"

  assert repr(x.lunch.rooster.protein) == "s.lunch.rooster.protein"
  assert repr(x.dinner[1].chicken.protein)== "s.dinner[1].chicken.protein"
  print x.dinner[1].chicken.protein

def test_NamedObject_list2():

  x = Human( nlunch=4, ndinner=1 )
  x.elaborate()

  assert repr(x) == "s"

  assert repr(x.lunch[3]) == "s.lunch[3]"
  assert repr(x.dinner) == "s.dinner"

  assert repr(x.lunch[3].rooster) == "s.lunch[3].rooster"
  assert repr(x.dinner.chicken) == "s.dinner.chicken"

  assert repr(x.lunch[3].rooster.protein) == "s.lunch[3].rooster.protein"
  assert repr(x.dinner.chicken.protein) == "s.dinner.chicken.protein"
  print repr(x.lunch[3].rooster.protein)
