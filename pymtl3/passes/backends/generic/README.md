### Translation Framework a.k.a. The "Generic" Backend

  - `behavioral/`
    - Includes the behavioral translator implementation and tests.
      - `L1` implements translation functionality for update blocks and free variables. The supported update block syntax
      at this level is the same as those supported by `BehavioralRTLIRGenL1` and `BehavioralRTLIRTypeCheckL1`.
      - `L2` through `L4` translators all call the behavioral generation and type check passes of the same level.
      - `L5` adds component hierarchy support by traversing the hierarchy and calling generation and type checking passes
      on each component.
      - The `L1` through `L5` translators are really for creating an incremental development narrative. Only the highest level `L5` is used by the top level `RTLIRTranslator`!

    - Users should not use translators under this directory -- use the `RTLIRTranslator` at the top level instead. These are
    only for framework testing purposes!
  - `structural/`
    - Includes the structural translator implementation and tests.
      - `L1` implements translation functionality for value ports/wires, arrays of signals. The supported PyMTL constructs
      at this level are the same as those supported by `StructuralRTLIRGenL1`.
      - `L2` adds support for `Struct` data type, and accessing attributes of a struct signal.
      - `L3` adds support for PyMTL interfaces, and accessing attribute signals of an interface.
      - `L4` adds component hierarchy support by traversing the hierarchy and calling the generation pass
      on each component.
      - The `L1` through `L4` translators are really for creating an incremental development narrative. Only the highest level `L4` is used by the top level `RTLIRTranslator`!

    - Users should not use translators under this directory -- use the `RTLIRTranslator` at the top level instead. These are
    only for framework testing purposes!
  - `RTLIRTranslator.py`
    - Customized backend translators should inherit from `RTLIRTranslator`.
    - `RTLIRTranslator` inherits from `BehavioralRTLIRTranslator` and `StructuralRTLIRTranslator` and composes the translated
    code segments after calling them.
    - It is possible to construct translators with different translation capabilities by calling `mk_RTLIRTranslator`, but
    this is only for framework testing purposes and users should avoid doing so.
