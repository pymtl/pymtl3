"""
========================================================================
set_param_test.py
========================================================================

Author : Yanhui Ou, Cheng Tan
Date   : May 28, 2019
"""
from pymtl3.datatypes.bits_import import Bits4, Bits8
from pymtl3.dsl.Component import Component
from pymtl3.dsl.ComponentLevel1 import update
from pymtl3.dsl.ComponentLevel3 import connect
from pymtl3.dsl.Connectable import InPort, OutPort
from pymtl3.dsl.NamedObject import NamedObject

from .sim_utils import simple_sim_pass


class Animal( NamedObject ):
  def construct( s, lunch="dirt", dinner="dirt" ):
    s.lunch  = lunch
    s.dinner = dinner

class AnimalHouse( NamedObject ):
  def construct( s, AnimalTypes=[] ):
    s.animals = [ A() for A in AnimalTypes ]

class HoneyBadger( Animal ):
  pass

class Dromaius( Animal ):
  pass

class Panda( Animal ):
  pass

class Tiger( Animal ):
  def construct( s, MeatTypes=[], lunch="dirt", dinner="dirt" ):
    s.meats  = [ Meat() for Meat in MeatTypes ]
    s.lunch  = lunch
    s.dinner = dinner

class BabyTiger( Tiger ):
  pass

class Aquarium( AnimalHouse ):
  pass

class TigerTerrace( AnimalHouse ):
  pass

class PandaHouse( AnimalHouse ):
  pass

class Zoo( NamedObject ):
  def construct( s, AnimalHouseTypes=[] ):
    s.houses = [ H() for H in AnimalHouseTypes ]

def test_simple():
  A = Dromaius()
  A.set_param( "top.construct", lunch="grass" )
  A.elaborate()

  print( A.lunch )
  assert A.lunch  == "grass"
  assert A.dinner == "dirt"

def test_set_param_overwrite():
  Z = Zoo()
  Z.set_param( "top.construct", AnimalHouseTypes=[ PandaHouse, TigerTerrace, AnimalHouse, Aquarium ] )
  Z.set_param( "top.houses[0].construct", AnimalTypes=[ Panda, Panda, Panda   ] )
  Z.set_param( "top.houses[1].construct", AnimalTypes=[ Tiger, BabyTiger      ] )
  Z.set_param( "top.houses[2].construct", AnimalTypes=[ Dromaius, HoneyBadger ] )
  Z.set_param( "top.houses[1].animals[0].construct", MeatTypes=[ Dromaius, HoneyBadger ] )
  Z.set_param( "top.houses[0].animals*.construct", lunch="bamboo", dinner="bamboo" )
  Z.set_param( "top.houses[1].animals[0].meats*.construct", lunch="bamboo" )
  Z.set_param( "top.houses[1].animals[0].meats[1].construct", lunch="grass" )
  # The following set_param test tricky overwrite behavior.
  Z.set_param( "top.houses[2].animals[0].construct", lunch="bugs", dinner="bugs" )
  Z.set_param( "top.houses[2].animals*.construct", lunch="grass" )
  Z.set_param( "top.houses[2].animals[0].construct", lunch="bugs" )
  Z.elaborate()

  assert isinstance( Z.houses[0], PandaHouse )
  assert isinstance( Z.houses[1], TigerTerrace )
  assert isinstance( Z.houses[2], AnimalHouse )
  assert isinstance( Z.houses[3], Aquarium )
  for i in range( 3 ):
    assert isinstance( Z.houses[0].animals[i], Panda )
    assert Z.houses[0].animals[i].lunch  == "bamboo"
    assert Z.houses[0].animals[i].dinner == "bamboo"

  assert isinstance( Z.houses[1].animals[0], Tiger )
  assert isinstance( Z.houses[1].animals[1], BabyTiger )
  assert Z.houses[1].animals[0].meats[0].lunch == "bamboo"
  assert Z.houses[1].animals[0].meats[1].lunch == "grass"

  assert isinstance( Z.houses[2].animals[0], Dromaius )
  assert isinstance( Z.houses[2].animals[1], HoneyBadger )
  # FIXME
  assert Z.houses[2].animals[0].lunch  == "bugs"
  assert Z.houses[2].animals[0].dinner == "bugs"
  assert Z.houses[2].animals[1].lunch  == "grass"
  assert Z.houses[2].animals[1].dinner == "dirt"

def test_multi_regex():
  Z = Zoo()
  Z.set_param( "top.construct", AnimalHouseTypes=[ PandaHouse, TigerTerrace, AnimalHouse, Aquarium ] )
  Z.set_param( "top.houses[0].construct", AnimalTypes=[ Panda, Panda, Panda   ] )
  Z.set_param( "top.houses[1].construct", AnimalTypes=[ Tiger, BabyTiger      ] )
  Z.set_param( "top.houses[2].construct", AnimalTypes=[ Dromaius, HoneyBadger ] )
  Z.set_param( "top.houses[0].animals[0].construct", lunch="potato", dinner="bamboo" )
  Z.set_param( "top.houses*.animals*.construct", lunch="onion" )
  Z.set_param( "top.houses*.animals[0].construct", lunch="potato" )
  Z.elaborate()

  assert Z.houses[0].animals[0].lunch  == "onion"
  assert Z.houses[0].animals[0].dinner == "bamboo"

def test_set_param_hierarchical():
  Z = Zoo()

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

def test_component():
  class Incr( Component ):
    def construct( s, DataType=Bits4, incr_value=1 ):
      s.in_ = InPort ( DataType )
      s.out = OutPort( DataType )

      s.incr_value = incr_value

      @update
      def up_incr():
        s.out @= s.in_ + s.incr_value

  class IncrArray( Component ):
    def construct( s, num_incrs=1, DataType=Bits4() ):
      s.in_ = [ InPort ( DataType ) for _ in range( num_incrs ) ]
      s.out = [ OutPort( DataType ) for _ in range( num_incrs ) ]

      s.incrs = [ Incr( DataType=DataType ) for _ in range( num_incrs ) ]

      for i in range( num_incrs ):
        connect( s.in_[i], s.incrs[i].in_ )
        connect( s.out[i], s.incrs[i].out )

  A = Incr()
  A.set_param( "top.construct", DataType=Bits8, incr_value=2 )
  A.elaborate()
  A.apply( simple_sim_pass )
  A.in_ = 1
  A.tick()
  print( "A.out==", A.out )
  assert A.out == 3

  B = IncrArray()
  B.set_param( "top.construct", DataType=Bits8, num_incrs=3 )
  B.set_param( "top.incrs*.construct", incr_value=3 )
  B.set_param( "top.incrs[2].construct", incr_value=5 )
  B.elaborate()
  B.apply( simple_sim_pass )
  B.in_[0] = 1
  B.in_[1] = 2
  B.in_[2] = 3
  B.tick()
  assert B.out[0] == 4
  assert B.out[1] == 5
  assert B.out[2] == 8
