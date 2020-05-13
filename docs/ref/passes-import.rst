External Verilog Import
=======================

PyMTL3 supports co-simulating external Verilog modules with PyMTL components
with the help of Verilator. If you have :ref:`set up Verilator <Set up Verilator for PyMTL3>`,
you should be able to import your Verilog designs, test their functionality
with productive Python-based testing strategies, or use them as submodules
of another PyMTL design.

Placeholder components
----------------------

`Placeholder` is a property of a PyMTL `Component` which indicates that this
component only declares its interface but leaves its implementation backed
by external designs (i.e., modules in Verilog source files). By declaring
components as having the `Placeholder` property, designers are able to concisely
describe a PyMTL component hierarchy in which one or multiple components backed
by external modules are interfaced to the rest of the hierarchy in a disciplined
way.

.. note:: A *placeholder* is often used interchangably with a *placeholder component*.

Example: a top-level Verilog placeholder
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is a full adder placeholder backed by an external Verilog module (indicated by
`VerilogPlaceholder`):

.. highlight:: python

::

    from pymtl3 import *
    class FullAdder( Component, VerilogPlaceholder ):
      def construct( s ):
        s.a = InPort( 1 )
        s.b = InPort( 1 )
        s.cin  = InPort( 1 )
        s.sum  = OutPort( 1 )
        s.cout = OutPort( 1 )

This placeholder only declares its interface but its implementation is supposed to
be backed by external modules. You will need this kind of placeholder if you want to
import an existing Verilog module for simulation.

Example: Verilog placeholder as submodule
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We can further build up a new PyMTL component that has placeholder subcomponents:

.. highlight:: python

::

    class HalfAdder( Component ):
      def construct( s ):
        s.a = InPort( 1 )
        s.b = InPort( 1 )
        s.sum = OutPort( 1 )
        s.cout = OutPort( 1 )
        s.adder = FullAdder()
        s.adder.a //= s.a
        s.adder.b //= s.b
        s.adder.cin //= 0
        s.adder.sum //= s.sum
        s.adder.cout //= s.cout

The component `HalfAdder` is no longer a placeholder -- it has a concrete PyMTL
implementation and it's implemented using the `FullAdder` placeholder.

Import-related passes
---------------------

A simulatable PyMTL component hierarchy must not have placeholders. We provide
import passes to replace the placeholders in the hierarchy with simulatable components.
For Verilog external modules, two passes need to be applied on the top-level component
so that the hierarchy is simulatable: `pymtl3.passes.backends.verilog.VerilogPlaceholderPass`
and `pymtl3.passes.backends.verilog.TranslationImportPass`. Both have been included when
you do `from pymtl3 import *`.

Example: import a PyMTL RTL component
-------------------------------------

We will demonstrate how to import a simple Verilog full adder. First let's make sure
the Verilog file `FullAdder.v` exists under the current working directory:

.. prompt:: bash $

   echo "\
   module FullAdder
   (
     input  logic clk,
     input  logic reset,
     input  logic a,
     input  logic b,
     input  logic cin,
     output logic cout,
     output logic sum
   );
     always_comb begin:
       sum = ( cin ^ a ) ^ b;
       cout = ( ( a ^ b ) & cin ) | ( a & b );
     end
   endmodule"> FullAdder.v

Then we will reuse the `FullAdder` placeholder in :ref:`a previous example <Example: a top-level Verilog placeholder>`
and apply the necessary import passes on it:

.. highlight:: python

::

    >>> m = FullAdder()
    >>> m.elaborate()
    >>> m.apply( VerilogPlaceholderPass() )
    >>> m = TranslationImportPass()( m )

Now `m` is a simulatable component hierarchy! Let's try to feed in data through its ports...

.. highlight:: python

::

    >>> m.apply( SimulationPass() )
    >>> m.sim_reset()
    >>> m.a @= 1
    >>> m.b @= 1
    >>> m.cin @= 1
    >>> m.sim_tick()
    >>> assert m.cout == 1
    >>> assert m.sum == 1

Once we have presented data to the ports of the full adder, we invoke `sim_tick` method to
evaluate the adder.

Translate-import
----------------

If you are using PyMTL3 for RTL designs, the framework also supports translating your
design and importing it back for simulation (which generally happens after you have
tested your design in a pure-Python environment). Since your design still exposes the
same interface, you can reuse your test harness and test cases for Python simulation
to test the translated Verilog design. This eliminates the need to develop Verilog
test harnesses and test cases, and also enables the use of Python features for productive
Verilog testing.

Example: translate-import the full adder
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will be using the full adder example from PyMTL3 in this demonstration. First let's
import the design:

.. highlight:: python

::

    >>> from pymtl3 import *
    >>> from pymtl3.examples.ex00_quickstart import FullAdder
    >>> m = FullAdder()
    >>> m.elaborate()

To translate-import this design, you will need to apply the two passes used in the previous
import example. Apart from that, since we are not importing a placeholder, we also need
to set up metadata to tell the translation-import pass to translate the full adder:

.. highlight:: python

::

    >>> m.set_metadata( TranslationImportPass.enable, True )
    >>> m.apply( VerilogPlaceholderPass() )
    >>> m = TranslationImportPass()( m )

Now we have a simulatable hierarchy backed by the translated Verilog full adder! You can
find the translation result `FullAdder_no_param__pickled.v` under the current working directory. You can also
simulate the adder like the following:

.. highlight:: python

::

    >>> m.apply( SimulationPass() )
    >>> m.sim_reset()
    >>> m.a @= 1
    >>> m.b @= 1
    >>> m.cin @= 1
    >>> m.sim_tick()
    >>> assert m.cout == 1
    >>> assert m.sum == 1
 
Common Verilog import questions
-------------------------------

How do I import a Verilog module whose ports use a SystemVerilog bitstruct?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Your PyMTL placeholder should declare a port of the same bitwidth.

How do I import a Verilog module having a port array?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
