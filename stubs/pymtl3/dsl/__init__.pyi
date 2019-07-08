from pymtl3.datatypes.bits_import import Bits
from typing import Callable
from .Connectable import *

class Component:

  # __init__ and construct are not annotated because they are dynamically
  # typed. Users are responsible for supplying type annotations for
  # BOTH __init__ and construct.

  # Construction time APIs

  def connect( s, u: ConnectableType, v: ConnectableType ) -> None: ...

  def update( s, func: Callable[[], None] ) -> Callable[[], None]: ...

  def update_on_edge( s, func: Callable[[], None] ) -> Callable[[], None]: ...

  # Post-construction APIs

  def elaborate( s ) -> None: ...
