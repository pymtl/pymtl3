PyMTL RTL Translation
=====================

For PyMTL3 RTL designs, the framework provides translation passes that
translate the RTL design into various backends (e.g., Verilog). A typical
PyMTL3 workflow starts from implementing and testing the DUT in the
Python environment. When the designer is confident about the correctness
of the DUT, he/she can simply apply the desired translation pass and use
the translation result to drive an ASIC or FPGA flow.

Translatable PyMTL RTL
----------------------

Translation passes only accept a translatable subset of all possible component
constructs. The following constructs are translatable:

- Structural constructs

  - Data types: all Bits and BitStruct types; list of translatable data types.
  - Constants: Python integer, Bits object, and BitStruct constant instance.
  - Signals: InPort, OutPort, and Wire of Bits or BitStruct type.
  - Interfaces: all interfaces whose all child interfaces are translatable.
  - Components: all components which have translatable interfaces, signals, and update blocks.
  - List of the translatable structural constructs.

- Behavioral constructs (update blocks)

  - ``@update``, ``@update_ff`` update blocks.
  - If-else statements
  - For-loop statements of single loop index whose range is specified through ``range()``
  - Assignment statements to signals through ``@=`` and ``<<=``
  - Assignment statements to temporary variables through ``=``

  - Constants: Python integer, Bits object, and BitStruct constant instance
  - Function calls

    - ``BitsN()``, ``BitStruct()``, ``zext()``, ``sext()``, ``trunc()``
  - Comparison between signals and constants
  - Arithmetic and logic operations between/on signals and constants

Some common non-translatable constructs include:

- use of common Python data structures including: set, dict, list of non-translatable constructs, etc.
- arbitrary function calls

Example: translate a PyMTL RTL component into Verilog
-----------------------------------------------------

We will demonstrate how to translate the full adder PyMTL RTL component that is included
in the PyMTL3 package. Note that if you are also interested in simulating the translated
component using PyMTL3, you might find :ref:`the translate-import feature <passes-import:Translate-import>`
useful because it translates the DUT and imports the translated module back for simulation.

First we need to import the full adder; the following code also dumps out how it is
implemented:

.. highlight:: python

::

    >>> from pymtl3 import *
    >>> from pymtl3.examples.ex00_quickstart import FullAdder
    >>> import inspect
    >>> print(inspect.getsource(FullAdder))
    class FullAdder( Component ):
      def construct( s ):
        s.a    = InPort( 1 )
        s.b    = InPort( 1 )
        s.cin  = InPort( 1 )
        s.sum  = OutPort( 1 )
        s.cout = OutPort( 1 )

        @update
        def upblk():
          s.sum = s.cin ^ s.a ^ s.b
          s.cout = ( ( s.a ^ s.b ) & s.cin ) | ( s.a & s.b )

To translate a component, it must have metadata that enables the
translation pass and the translation pass needs to be applied on it. The following code
shows how these can be done. The name ``TranslationPass``, which refers to the Verilog
translation pass, has already been included previously when we did
``from pymtl3 import *``. Note that you can set metadata of a component anytime after
that object has been created, but you should only apply the translation pass after it
has been elaborated.

.. highlight:: python

::

    >>> m = FullAdder()
    >>> m.elaborate()
    >>> m.set_metadata( TranslationPass.enable, True )
    >>> m.apply( TranslationPass() )

After that you should be able to inspect the translated Verilog code in the current
working directory.

.. prompt:: bash $

    less FullAdder_noparam__pickled.v

The string ``noparam`` indicates this translation result came from
a PyMTL component whose ``construct`` method requires no arguments except for the self
object ``self``. If the DUT had extra arguments, those will contribute to this string.
And the suffix ``__pickled`` indicates the translation result is a standalone Verilog
source file that can be used to drive an ASIC or FPGA flow. In fact, this is true for
all PyMTL translation results with the exception being your hierarchy includes a
:doc:`Verilog placeholder <passes-import:Verilog Placeholder>` whose source file assumes
an implicit Verilog include path.
