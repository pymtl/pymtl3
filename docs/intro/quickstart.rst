.. Documentation pointing to quick start examples

Quick Start Guide
=================

This guide demonstrates how to perform arithmetics on the PyMTL3
Bits objects and how to simulate simple hardware components like
a full adder and a register incrementer. All contents of this
guide can be finished in a Python >= 3.6 interative REPL.

Bits arithmetics
----------------

Let's start with a simple addition of two 4-bit numbers. The
following code snippet imports the basic PyMTL3 functionalities
and creates two 4-bit objects ``a`` and ``b``:

.. highlight:: python

::

    >>> from pymtl3 import *
    >>> a = Bits4(4)
    Bits4(0x4)
    >>> b = Bits4(3)
    Bits4(0x3)

The Bits objects support common arithmetics and comparisons:

.. highlight:: python

::

    >>> a + b
    Bits4(0x7)
    >>> a - b
    Bits4(0x1)
    >>> a * b
    Bits4(0xC)
    >>> a & b
    Bits4(0x0)
    >>> a | b
    Bits4(0x7)
    >>> a > b
    Bits1(0x1)
    >>> a < b
    Bits1(0x0)

Full adder example
------------------

Next we will experiment with a full adder. It has already been
included in the PyMTL3 code base and we can simply import it
to use it in the REPL.

.. highlight:: python

::

    >>> from pymtl3.examples.ex00_quickstart import FullAdder

Thanks to the inspection feature of Python we can easily print
out the source code of the full adder. You can see that the
full adder logic is implemented inside an update block ``upblk``.

.. highlight:: python

::

    >>> import inspect
    >>> print(inspect.getsource(FullAdder))
    class FullAdder( Component ):
      def construct( s ):
        s.a    = InPort()
        s.b    = InPort()
        s.cin  = InPort()
        s.sum  = OutPort()
        s.cout = OutPort()

        @update
        def upblk():
          s.sum  @= s.cin ^ s.a ^ s.b
          s.cout @= ( ( s.a ^ s.b ) & s.cin ) | ( s.a & s.b )

To simulate the full adder, we need to apply the ``DefaultPassGroup``
PyMTL pass. Then we can set the value of input ports and simulate
the full adder by calling ``fa.sim_tick``:

.. highlight:: python

::

    >>> fa = FullAdder()
    >>> fa.apply( DefaultPassGroup() )
    >>> fa.sim_reset()
    >>> fa.a @= 0
    >>> fa.b @= 1
    >>> fa.cin @= 0
    >>> fa.sim_tick()

Now let's verify that the full adder produces the correct result:

.. highlight:: python

::

    >>> assert fa.sum == 1
    >>> assert fa.cout == 0

Register incrementer example
----------------------------

Similar to the full adder, we can do the following to import the
register incrementer component and print out its source:

.. highlight:: python

::

    >>> from pymtl3.examples.ex00_quickstart import RegIncr
    >>> print(inspect.getsource(RegIncr))

And to simulate an 8-bit register incrementer:

.. highlight:: python

::

    >>> regincr = RegIncr( 8 )
    >>> regincr.apply( DefaultPassGroup() )
    >>> regincr.sim_reset()
    >>> regincr.in_ @= 42
    >>> regincr.sim_tick()

Now verify the registered output is indeed incremented:

.. highlight:: python

::

    >>> assert regincr.out == 43
