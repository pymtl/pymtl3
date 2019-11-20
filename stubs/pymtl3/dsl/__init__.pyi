from pymtl3.datatypes import BitsN, Bits1

from typing import *

#-------------------------------------------------------------------------
# get_nbits
#-------------------------------------------------------------------------

def get_nbits( Type: int ) -> int: ...

#-------------------------------------------------------------------------
# mk_bits
#-------------------------------------------------------------------------

def mk_bits( nbits: int ) -> BitsN: ...

#-------------------------------------------------------------------------
# Interface
#-------------------------------------------------------------------------

class Interface: ...

#-------------------------------------------------------------------------
# Component
#-------------------------------------------------------------------------

class Component:

  def __init__( s, *args, **kwargs ) -> None: ...

  def apply( s, passes: Any ) -> None: ...
  def update( s, func: Any ) -> None: ...
  def update_on_edge( s, func: Any ) -> None: ...
  def elaborate( s ) -> None: ...

#-------------------------------------------------------------------------
# Signal
#-------------------------------------------------------------------------

# Making T_SignalDataType covariant enables the following useful subtyping
#   e.g. Signal[Bits1] < Signal[BitsN]
T_SignalDataType = TypeVar("T_SignalDataType", covariant=True)

class Signal(Generic[T_SignalDataType]):

  @overload
  def __init__( s ) -> None: ...

  @overload
  def __init__( s, value: int ) -> None: ...

  # Directionality-agnostic assignment in upblks
  def __set__( s, obj: Component, value: Signal[T_SignalDataType] ) -> None: ...

  # Note that since the AoT type checker is meant to be directionality-agnostic,
  # it does not matter whether we return Signal[Any] or just Any.
  # This helps the type cheker infer the correct type of an argument to `connect`
  # if the other argument has non-static data type (e.g. a slice of some port).

  # getting a slice from a vector
  @overload
  def __getitem__( s, index: int ) -> Signal[Bits1]: ...

  # This Bits1 will be overwritten at run-time
  @overload
  def __getitem__( s, index: slice ) -> Signal[Bits1]: ...
  # def __getitem__( s, index: slice ) -> Signal[BitsN]: ...

  # setting a slice of a vector
  @overload
  def __setitem__( s, index: int, value: Signal[Bits1] ) -> Any: ...

  @overload
  def __setitem__( s, index: slice, value: Signal[BitsN] ) -> Any: ...

  # Signal operators

  def __invert__( s ) -> Signal[T_SignalDataType]: ...
  def __sub__( s, other: Signal[T_SignalDataType] ) -> Signal[T_SignalDataType]: ...
  def __and__( s, other: Signal[T_SignalDataType] ) -> Signal[T_SignalDataType]: ...
  def __add__( s, other: Signal[T_SignalDataType] ) -> Signal[T_SignalDataType]: ...

#-------------------------------------------------------------------------
# InPort
#-------------------------------------------------------------------------

T_InPortDataType = TypeVar("T_InPortDataType", covariant=True)

class InPort(Signal[T_InPortDataType]): ...

#-------------------------------------------------------------------------
# OutPort
#-------------------------------------------------------------------------

T_OutPortDataType = TypeVar("T_OutPortDataType", covariant=True)

class OutPort(Signal[T_OutPortDataType]): ...

#-------------------------------------------------------------------------
# Wire
#-------------------------------------------------------------------------

T_WireDataType = TypeVar("T_WireDataType", covariant=True)

class Wire(Signal[T_WireDataType]): ...

#-------------------------------------------------------------------------
# Const
#-------------------------------------------------------------------------

T_ConstDataType = TypeVar("T_ConstDataType", covariant=True)

class Const(Signal[T_ConstDataType]):

  @overload
  def __init__( s, value: int = 0 ) -> None: ...

  @overload
  def __init__( s, value: Signal[BitsN] ) -> None: ...

  @overload
  def __init__( s, Type: Any, value: int, parent: Any ) -> None: ...

#-------------------------------------------------------------------------
# connect
#-------------------------------------------------------------------------

# T_connect = TypeVar( "T_connect", covariant=True, bound=BitsN)
T_connect = TypeVar( "T_connect" )

def connect( u: Signal[T_connect], v: Signal[T_connect] ) -> None: ...

#-------------------------------------------------------------------------
# RList
#-------------------------------------------------------------------------
# RList means "RTL-List". I didn't use the built-in List type because
# an assignment to List[T] requires the RHS to be of T, which is not true
# for our DSL. We use __set__ workaround for Signals and we also need to
# special-case lists.

T_RListItemType = TypeVar("T_RListItemType")
T_RListDataType = TypeVar("T_RListDataType")

class RList(Generic[T_RListItemType, T_RListDataType]):

  def __setitem__( s, index: int, value: Signal[T_RListDataType] ) -> None: ...

  def __getitem__( s, index: Union[int, Signal[BitsN]] ) -> T_RListItemType: ...
