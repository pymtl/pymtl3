"""
========================================================================
set_param_test.py
========================================================================

Author : Yanhui Ou, Cheng Tan
Date   : May 28, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3.dsl.NamedObject import NamedObject

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

class Tiger( NamedObject ):
  def construct( s, MeatTypes=[], lunch="dirt", dinner="dirt" ):
    s.meats  = [ Meat() for Meat in MeatTypes ]
    s.lunch  = lunch
    s.dinner = dinner

class Aquarium( NamedObject ):
  def construct( s, AnimalTypes=[], AnimalHouseTypes=[] ):
    s.animals = [ A() for A in AnimalTypes ]
    s.houses = [ H() for H in AnimalHouseTypes ]

class TigerTerrace( NamedObject ):
  def construct( s, AnimalTypes=[], AnimalHouseTypes=[] ):
    s.animals = [ A() for A in AnimalTypes ]
    s.houses = [ H() for H in AnimalHouseTypes ]

class Zoo( NamedObject ):
  def construct( s, AnimalTypes=[], AnimalHouseTypes=[] ):
    s.animals = [ A() for A in AnimalTypes ]
    s.houses = [ H() for H in AnimalHouseTypes ]

def test_set_param_overwrite():
  A = Dromaius()
  A.set_param( "top.construct", lunch="grass" )
  A.elaborate()

  print( A.lunch )
  assert A.lunch  == "grass" 
  assert A.dinner == "dirt" 

  Z = Zoo()
  Z.set_param( "top.construct", AnimalTypes=[ HoneyBadger, Dromaius, Panda ] )
  Z.set_param( "top.construct", AnimalHouseTypes=[ Aquarium, TigerTerrace ] )
  Z.set_param( "top.houses[1].construct", AnimalTypes=[ Tiger, Panda ] )
  Z.set_param( "top.houses[1].animals[0].construct", MeatTypes=[ Panda, Tiger ] )
  Z.set_param( "top.houses[1].animals[0].meats*.construct", lunch="bamboo" )
  Z.set_param( "top.houses[1].animals[0].meats[1].construct", lunch="grass" )
  Z.set_param( "top.animals[0].construct", dinner="bamboo" )
  Z.set_param( "top.animals*.construct", 
      lunch ="grass",
      dinner="poisoned onion"
  )
  Z.set_param( "top.animals[2].construct", dinner="bamboo" )
  Z.set_param( "top.animals[1].construct", lunch=Panda() )
  Z.set_param( "top.animals[1].lunch.construct", lunch=Dromaius() )
  Z.set_param( "top.animals[1].lunch.lunch.construct", lunch="bug" )

  Z.elaborate()

  assert Z.animals[0].lunch  == "grass"
  assert Z.animals[0].dinner == "poisoned onion"
  assert Z.animals[1].dinner == "poisoned onion"
  assert Z.animals[2].lunch  == "grass"
  assert Z.animals[2].dinner == "bamboo"
  assert isinstance(Z.animals[1].lunch, Panda)
  assert isinstance(Z.animals[1].lunch.lunch, Dromaius)
  assert Z.animals[1].lunch.lunch.lunch == "bug"
  assert isinstance(Z.houses[1], TigerTerrace)
  assert Z.houses[1].animals[0].meats[0].lunch == "bamboo"
  assert Z.houses[1].animals[0].meats[1].lunch == "grass"

def test_set_param_hierarchical():

  Z = Zoo()

  Z.set_param( "top.construct", AnimalTypes=[ HoneyBadger, Dromaius, Panda ] )
  Z.set_param( "top.construct", AnimalHouseTypes=[ Aquarium, TigerTerrace ] )
  Z.set_param( "top.houses[1].construct", AnimalTypes=[ Tiger, Panda ] )
  Z.set_param( "top.houses*.animals*.construct", lunch="grass" )
  Z.set_param( "top.houses*.animals[1].construct", lunch="meat" )

  #TODO: Whether we should check throw an error in following scenario
  Z.set_param( "top.houses*.xxx*.construct", lunch="grass" )

  Z.elaborate()

  assert isinstance(Z.houses[1], TigerTerrace)
  assert Z.houses[1].animals[0].lunch == "grass"
  assert Z.houses[1].animals[1].lunch == "meat"


