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
        s.a = InPort()
        s.b = InPort()
        s.cin  = InPort()
        s.sum  = OutPort()
        s.cout = OutPort()

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
        s.a = InPort()
        s.b = InPort()
        s.sum = OutPort()
        s.cout = OutPort()
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
and `pymtl3.passes.backends.verilog.VerilogTranslationImportPass`. Both have been included when
you do `from pymtl3.passes.backends.verilog import *`.

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

    >>> from pymtl3.passes.backends.verilog import *
    >>> m = FullAdder()
    >>> m.elaborate()
    >>> m.apply( VerilogPlaceholderPass() )
    >>> m = VerilogTranslationImportPass()( m )

Now `m` is a simulatable component hierarchy! Let's try to feed in data through its ports...

.. highlight:: python

::

    >>> m.apply( DefaultPassGroup() )
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

    >>> from pymtl3.passes.backends.verilog import *
    >>> m.set_metadata( VerilogTranslationImportPass.enable, True )
    >>> m.apply( VerilogPlaceholderPass() )
    >>> m = VerilogTranslationImportPass()( m )

Now we have a simulatable hierarchy backed by the translated Verilog full adder! You can
find the translation result `FullAdder_no_param__pickled.v` under the current working
directory. You can also simulate the adder like the following:

.. highlight:: python

::

    >>> m.apply( DefaultPassGroup() )
    >>> m.sim_reset()
    >>> m.a @= 1
    >>> m.b @= 1
    >>> m.cin @= 1
    >>> m.sim_tick()
    >>> assert m.cout == 1
    >>> assert m.sum == 1

Advanced Verilog import
-----------------------

These import features make use of options offered by `VerilogPlaceholderPass` and
`VerilogVerilatorImportPass`. In general, the options related to the Verilog module and
source files are class attributes of `VerilogPlaceholderPass`; the options
related to Verilator and C++ simulator compilation are class attributes of `VerilogVerilatorImportPass`.

While technically PyMTL is able to import any Verilatable Verilog design, code that conforms to
certain rules can be imported much easier. For example, "pickled" designs are easier to import
because having a standalone file saves the hassle of specifying its dependent files; we also
recommend adding an `ifndef *unique_label*` guard to every file to avoid potential duplicated
definitions during import.

How do I specify the file name and module name of the target design?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Assuming you would like to import module `FooBar` from file `FooBarModule.v` in the
same directory as the Python file that defines its wrapper `PyMTLFooBar`, you can
set the `src_file` and `top_module` options on the placeholder `PyMTLFooBar`:

.. highlight:: python

::

    from os import path
    class PyMTLFooBar( Component, Placeholder ):
      def construct( s ):
        # interface declaration here
        ...
        # Name of the top level module to be imported
        s.set_metadata( VerilogPlaceholderPass.top_module, 'FooBar' )
        # Source file path
        s.set_metadata( VerilogPlaceholderPass.src_file, path.dirname(__file__) + '/FooBarModule.v' )

If you don't specify these two options, the default value of `top_module` will be the class
name of the placeholder (e.g., `PyMTLFooBar`) and the default value of `src_file` will be
`<top_module>.v` (e.g., `PyMTLFooBar.v`).

How do I specify the parameters of the target module?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Assuming you are trying to import a module with parameter `nbits = 32`. There are two ways to do that.

First you can directly add that parameter to the `construct` method of your placeholder like the following

.. highlight:: python

::

    class PyMTLFooBar( Component, Placeholder ):
      def construct( s, nbits ):
        # interface declaration here
        ...

The import pass will assume the module to be imported has a parameter named `nbits` whose value is
determined during the elaboration of the PyMTL component hierarchy.

The second approach requires setting the `params` option like this:

.. highlight:: python

::

    class PyMTLFooBar( Component, Placeholder ):
      def construct( s, pymtl_nbits ):
        # interface declaration here
        ...
        s.set_metadata( VerilogPlaceholderPass.params, {
          'nbits' : pymtl_nbits
        } )

The `params` option takes a Python dictionary that maps parameter names (strings) to integers. When
both `construct` arguments and the `params` option are present, the import pass prioritizes the
explicit `params` option over `construct` arguments.

What if my target module does not have clk/reset pins?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

PyMTL3 assumes each component has implicit `clk` and `reset` pins. By default, the import pass scans
through the target Verilog file and tries to find code that defines a single-bit `clk` or `reset` pins.
If you are importing a small design (maybe only a single module), this should work well and eliminate
the need to manually specify whether your Verilog module has `clk` or `reset`.

If you wish to explicitly mark some placeholder as having or not having `clk`/`reset`, you can set the
`has_clk` and `has_reset` options like this

.. highlight:: python

::

    class PyMTLFooBar( Component, Placeholder ):
      def construct( s ):
        # interface declaration here
        ...
        s.set_metadata( VerilogPlaceholderPass.has_clk, False )
        s.set_metadata( VerilogPlaceholderPass.has_reset, True )

The explicit `has_clk` and `has_reset` options have priority over the values inferred from the Verilog
source file.

What if my target module requires a Verilog include path?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can set the `v_include` option to a list of absolute path of include directories. Note that the
current implementation only supports up to one include path.

.. highlight:: python

::

    from os import path
    class PyMTLFooBar( Component, Placeholder ):
      def construct( s ):
        # interface declaration here
        ...
        s.set_metadata( VerilogPlaceholderPass.v_include, [path.dirname(__file__)] )

The above code snippet adds the directory that contains this file to the Verilog include path during
import. Note that if you use placeholders with `v_include` metadata as sub-components, then during
translation-import the top-level component will automatically get `v_include` metadata aggregated
across all placeholders in that hierarchy.

What if my target module depends on other Verilog files?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can set the `v_libs` option to provide a list of Verilog source files to be used together with
the target source file. Suppose Verilog file `PyMTLFooBar.v` depends on `PyMTLFooBarDependency.v`,
the following code snippet adds the dependency file to help Verilator resolve all definitions.

.. highlight:: python

::

    from os import path
    class PyMTLFooBar( Component, Placeholder ):
      def construct( s ):
        # interface declaration here
        ...
        s.set_metadata( VerilogPlaceholderPass.v_libs, [path.dirname(__file__) + '/PyMTLFooBarDependency.v'] )

Note that the files specified through `v_libs` will appear in the translation result if you translate
a hierarchy that includes such placeholders.

What if the PyMTL component port names are different from Verilog port names?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can use the `port_map` option which is a dictionary mapping ports to the name of Verilog port
names (strings). The following code snippet shows how to map the PyMTL port names `in_` and `out`
to Verilog port names `d` and `q`.

.. highlight:: python

::

    class Register( Component, Placeholder ):
      def construct( s ):
        s.in_ = InPort()
        s.out = OutPort()
        s.set_metadata( VerilogPlaceholderPass.port_map, {
          s.in_ : 'd',
          s.out : 'q',
        } )

How to enable Verilator coverage?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can set option `vl_coverage`, `vl_line_coverage`, and `vl_toggle_coverage` to enable Verilator
coverage (`--coverage`), line coverage (`--coverage-line`), and toggle coverage (`--coverage-toggle`).

.. highlight:: python

::

    class PyMTLFooBar( Component, Placeholder ):
      def construct( s ):
        # interface declaration here
        ...
        s.set_metadata( VerilogVerilatorImportPass.vl_coverage, True )
        s.set_metadata( VerilogVerilatorImportPass.vl_line_coverage, True )
        s.set_metadata( VerilogVerilatorImportPass.vl_toggle_coverage, True )

How to suppress certian Verilator warnings?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is a code snipeet that disables lint, style, and fatal warnings. It also suppresses the `MODDUP`
warning. `vl_Wno_list` takes a list of warning names to be suppressed.

.. highlight:: python

::

    class PyMTLFooBar( Component, Placeholder ):
      def construct( s ):
        # interface declaration here
        ...
        s.set_metadata( VerilogVerilatorImportPass.vl_W_lint, False )
        s.set_metadata( VerilogVerilatorImportPass.vl_W_style, False )
        s.set_metadata( VerilogVerilatorImportPass.vl_W_fatal, False )
        s.set_metadata( VerilogVerilatorImportPass.vl_Wno_list, [ 'MODDUP' ] )

How to dump VCD from the Verilator-Python co-simulation?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is a code snipeet that enables VCD dumping to `DUT.vcd`, sets time scale to `1ps`, sets the `clk` pin
cycle to `10 * 1ps = 10ps`.

.. highlight:: python

::

    class PyMTLFooBar( Component, Placeholder ):
      def construct( s ):
        # interface declaration here
        ...
        s.set_metadata( VerilatorImportPass.vl_trace, True )
        s.set_metadata( VerilatorImportPass.vl_trace_filename, 'DUT.vcd' )
        s.set_metadata( VerilatorImportPass.vl_trace_timescale, '1ps' )
        s.set_metadata( VerilatorImportPass.vl_trace_cycle_time, 10 )

How to enable Verilog line_trace function?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your Verilog module defines the `line_trace` function using macro `VC_TRACE_BEGIN/END`, you can
enable Verilog line trace like this

.. highlight:: python

::

    class PyMTLFooBar( Component, Placeholder ):
      def construct( s ):
        # interface declaration here
        ...
        s.set_metadata( VerilogVerilatorImportPass.vl_line_trace, True )

Is it possible to add source files, include paths, or flags to the C compiler?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: This feature has not been thoroughly tested.

If your Verilog simulation requires external C sources, include paths, or flags,
you can specify them through the following options provided by `VerilogVerilatorImportPass`:
`c_flags` (string), `c_include_path` (a list of paths), `c_srcs` (a list of paths),
`ld_flags` (string), `ld_libs` (string).

Common Verilog import questions
-------------------------------

How do I import a Verilog module whose ports use a SystemVerilog bitstruct?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Your PyMTL placeholder should declare a port of the same bitwidth.

How do I import a Verilog module whose port name is `in`?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

That is not supported because `in` is a Python reserved keyword. We recommend
changing the port name (i.e., to `in_`).

How do I import a Verilog module with a port array?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your module has an unpacked array port like this

.. highlight:: verilog

::

    module foo(
      input logic [31:0] foo_in [0:2][0:3]
    );
      ...
    endmodule

you will need an array of input ports like the following

.. highlight:: python

::

    class foo( Component, VerilogPlaceholder ):
      def construct( s ):
        # This creates a 4x3 input port array which matches the Verilog module
        s.foo_in = [ [ InPort(32) for _ in range(4) ] for _ in range(3) ]
        ...

If your module has a packed array port like this

.. highlight:: verilog

::

    module foo(
      input logic [2:0][3:0][31:0] foo_in
    );
      ...
    endmodule

you will need one input port of a long vector like the following

.. highlight:: python

::

    class foo( Component, VerilogPlaceholder ):
      def construct( s ):
        # This creates one input port whose width matches the Verilog module
        s.foo_in = InPort(3*4*32)
        ...
