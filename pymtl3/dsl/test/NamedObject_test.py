"""
========================================================================
NamedObject_test.py
========================================================================

Author : Shunning Jiang
Date   : Dec 23, 2017
"""
from pymtl3.dsl.errors import FieldReassignError
from pymtl3.dsl.NamedObject import NamedObject


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
    else:           s.lunch = [ Tiger() for _ in range(nlunch) ]

    if ndinner == 1: s.dinner = Dog()
    else:            s.dinner = [ Dog() for _ in range(ndinner) ]

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
  print(x.dinner.chicken.protein)

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
  print(x.dinner[1].chicken.protein)

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
  print(repr(x.lunch[3].rooster.protein))

# FIXME
def test_use_init_error():

  class Crocodile(NamedObject):

    def __init__( s ):
      s.food = Dog()
      print(s.food.chicken)

  # x = Chicken()
  # x.elaborate()
  # y = Crocodile()
  # y.elaborate()
  # z = Chicken()
  # z.elaborate()

def test_invalid_reassignment_attr():

  class Donkey( NamedObject ):
    def construct( s ):
      s.x = Dog()
      s.x = Dog()

  x = Donkey()
  try:
    x.elaborate()
  except FieldReassignError as e:
    print(e)
    assert str(e).startswith("The attempt to assign hardware construct to field")
    return
  raise Exception("Should've thrown FieldReassignError")

def test_invalid_reassignment_list():

  class Donkey( NamedObject ):
    def construct( s ):
      s.x = Dog()
      s.x = [ Dog() for _ in range(4) ]

  x = Donkey()
  try:
    x.elaborate()
  except FieldReassignError as e:
    print(e)
    assert str(e).startswith("The attempt to assign hardware construct to field")
    return
  raise Exception("Should've thrown FieldReassignError")

def test_set_param():

  class HoneyBadger( NamedObject ):
    def construct( s, lunch="dirt", dinner="dirt" ):
      s.lunch  = lunch
      s.dinner = dinner

  class Dromaius( NamedObject ):
    def construct( s, lunch="dirt", dinner="dirt" ):
      s.lunch  = lunch
      s.dinner = dinner

  class Panda( NamedObject ):
    def construct( s, lunch="dirt", dinner="dirt" ):
      s.lunch  = lunch
      s.dinner = dinner

  class Zoo( NamedObject ):
    def construct( s, AnimalTypes=[] ):
      s.animals = [ A() for A in AnimalTypes ]

  A = Dromaius()
  A.set_param( "top.construct", lunch="grass" )
  A.elaborate()

  print( A.lunch )
  assert A.lunch  == "grass"
  assert A.dinner == "dirt"

  Z = Zoo()
  Z.set_param( "top.construct", AnimalTypes=[ HoneyBadger, Dromaius, Panda ] )
  Z.set_param( "top.animals[0].construct", dinner="bamboo" )
  Z.set_param( "top.animals*.construct",
      lunch ="grass",
      dinner="poisoned onion",
  )
  Z.set_param( "top.animals[2].construct", dinner="bamboo" )
  print( "="*30, "Z", "="*30 )
  print( Z._dsl.param_tree.leaf )
  print( Z._dsl.param_tree.children )
  print( "="*30, "Z.animals[0]", "="*30 )
  print( Z._dsl.param_tree.children["animals[0]"].leaf )
  print( Z._dsl.param_tree.children["animals[0]"].children )
  print( "="*30, "Z.animals*", "="*30 )
  print( Z._dsl.param_tree.children["animals*"].leaf )
  print( Z._dsl.param_tree.children["animals*"].children )
  print( "="*30, "Z.animals[2]", "="*30 )
  print( Z._dsl.param_tree.children["animals[2]"].leaf )
  print( Z._dsl.param_tree.children["animals[2]"].children )
  Z.elaborate()
  print( "="*30, "animals[0]", "="*30 )
  print( Z.animals[0]._dsl.param_tree.leaf )
  print( Z.animals[1]._dsl.param_tree.children )
  print( "="*30, "animals[1]", "="*30 )
  print( Z.animals[0]._dsl.param_tree.leaf )
  print( Z.animals[1]._dsl.param_tree.children )
  print( "="*30, "animals[2]", "="*30 )
  print( Z.animals[0]._dsl.param_tree.leaf )
  print( Z.animals[1]._dsl.param_tree.children )

  assert Z.animals[0].lunch  == "grass"
  assert Z.animals[1].lunch  == "grass"
  assert Z.animals[2].lunch  == "grass"
  assert Z.animals[0].dinner == "poisoned onion"
  assert Z.animals[1].dinner == "poisoned onion"
  assert Z.animals[2].dinner == "bamboo"
