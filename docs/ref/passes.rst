Passes
======

Simulation passes
-----------------

.. autoclass:: pymtl3.passes.PassGroups.SimulationPass
   :members:
   :special-members:
   :private-members:
   :undoc-members:

.. autoclass:: pymtl3.passes.PassGroups.SimpleSimPass
   :members:
   :special-members:
   :private-members:
   :undoc-members:

.. autoclass:: pymtl3.passes.PassGroups.AutoTickSimPass
   :members:
   :special-members:
   :private-members:
   :undoc-members:

Translation passes
------------------

Verilog translation pass
^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: pymtl3.passes.backends.verilog.translation.TranslationPass.TranslationPass

   .. automethod:: __init__
   .. automethod:: __call__

Here are the available input and output metadata of the Verilog translation pass:

.. autoclass:: pymtl3.passes.backends.verilog.translation.TranslationPass.TranslationPass
   :members:

Yosys translation pass
^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: pymtl3.passes.backends.yosys.translation.TranslationPass.TranslationPass

   .. automethod:: __init__
   .. automethod:: __call__

The available input and output metadata of the Yosys translation pass are the same
as those of the :ref:`Verilog translation pass <Verilog translation pass>`.

Import passes
-------------

.. autoclass:: pymtl3.passes.backends.verilog.import_.VerilatorImportPass.VerilatorImportPass
   :members:
   :special-members:
   :private-members:
   :undoc-members:

.. autoclass:: pymtl3.passes.backends.yosys.import_.VerilatorImportPass.VerilatorImportPass
   :members:
   :special-members:
   :private-members:
   :undoc-members:

Translation-import passes
-------------------------

.. autoclass:: pymtl3.passes.backends.verilog.TranslationImportPass.TranslationImportPass
   :members:
   :special-members:
   :private-members:
   :undoc-members:

.. autoclass:: pymtl3.passes.backends.yosys.TranslationImportPass.TranslationImportPass
   :members:
   :special-members:
   :private-members:
   :undoc-members:

Placeholder passes
------------------

.. autoclass:: pymtl3.passes.backends.verilog.VerilogPlaceholderPass.VerilogPlaceholderPass
   :members:
   :special-members:
   :private-members:
   :undoc-members:
