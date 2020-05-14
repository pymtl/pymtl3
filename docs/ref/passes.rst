Passes
======

PyMTL Passes are modular Python programs that can be applied on PyMTL components to analyze,
instrument, or transform the given component hierarchy.

Communicate with passes using metadata
--------------------------------------

Metadata are per-component data that can be used to customize the behavior of various passes.
PyMTL components provide two APIs to set and retrieve metadata: `Component.set_metadata(key, value)`
and `Component.get_metadata(key)`, where `key` must be an instance of `MetadataKey` and `value`
can be an arbitrary Python object.

PyMTL passes whose behavior can be customized are required to declare their customizable options
as a `MetadataKey` class attributes of the pass. For example, you can see the list of supported
options of `VerilatorImportPass` :ref:`here <Verilog import pass>`. To enable the import pass on
a component `m`, you can set the metadata like this

.. highlight:: python

::

    m.set_metadata( VerilatorImportPass.enable, True )

and the import pass will be able to pick up this metadata when it is applied.

If the pass you are interested in does not support customizable options or the default options
can achieve what you want, you are not required to set any metadata.

Simulation passes
-----------------

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Simulation passes

   passes-sim-api

:doc:`API reference <passes-sim-api>`

Translation passes
------------------

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Translation passes

   passes-translation-intro
   passes-translation-meta

:doc:`Introduction <passes-translation-intro>` | :doc:`Metadata reference <passes-translation-meta>`

Import passes
-------------

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Import passes

   passes-import-intro
   passes-import-meta

:doc:`Introduction <passes-import-intro>` | :doc:`Metadata reference <passes-import-meta>`

Translation-import passes
-------------------------

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Translation-import passes

   passes-trans-import-meta

:doc:`Metadata reference <passes-trans-import-meta>`

Placeholder passes
------------------

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Placeholder passes

   passes-placeholder-meta

:doc:`Metadata reference <passes-placeholder-meta>`
