# RTLIR
  - `__init__.py`
    - Exposes passes that generate or analyze RTLIR to the user.
      - `BehavioralRTLIRGenPass` generates the behavioral RTLIR for a PyMTL object.
      - `BehavioralRTLIRTypeCheckPass` type checks the generated behavioral RTLIR.
      - `BehavioralVisualizationPass` visualizes the generated behavioral RTLIR and dumps it into a PDF file.
      - `StructuralRTLIRGenPass` generates the structural RTLIR for a PyMTL object.
    - Exposes methods that generate RTLIR for a single Python object.
      - `is_rtlir_convertible` return `True` if the given object can be converted to RTLIR.
      - `get_rtlir` returns the RTLIR representation of the given object.
      - `get_rtlir_dtype` returns the RTLIR data type of the given object.
    - Also exposes modules that contain the definitions of RTLIR-related classes
      - `BehavioralRTLIR` includes the definitions of all classes that can appear in an IR AST for an update block.
      - `RTLIRType` includes the definitions of all possible RTLIR instance classes.
      - `RTLIRDataType` includes the definitions of all possible RTLIR data type classes.
      - `StructuralSignalExpr` includes the definitions of all possible operations that can appear in an IR signal expression.
  - `rtype/`
    - This folder contains files that implement the classes of RTLIR instances and data types.
  - `behavioral/`
    - This folder contains implementation and test cases of the behavioral part of RTLIR.
    - The passes related to behavioral RTLIR are developed incrementally
      - `L1` is the initial implementation and only supports assignments, value ports, integer constants, and free variables.
      - `L2` adds support for `If`, `For`, comparisons, arithmetic operations, and temporary variables.
      - `L3` adds support for `Struct` data type.
      - `L4` adds support for PyMTL interface.
      - `L5` adds support for component hierarchy.
      - The `L1` through `L5` passes are really for creating an incremental development narrative to avoid having all
      methods in a gigantic class. Only the highest level `L5` is and should be used by other passes!
    - The user should only use passes exposed through the top level `__init__.py`. The other passes are used for
    framework testing purposes.
  - `structural/`
    - This folder contains implementation and test cases of the structural part of RTLIR.
    - The passes related to structural RTLIR are developed incrementally
      - `L1` is the initial implementation and only supports value ports/wires, integer constants, and connections between them.
      - `L2` adds support for `Struct` data type, and accessing attributes of a `Struct` signal.
      - `L3` adds support for PyMTL interface, and accessing attribute signals of an interface.
      - `L4` adds support for component hierarchy, and connecting ports of components.
      - The `L1` through `L4` passes are really for creating an incremental development narrative to avoid having all
      methods in a gigantic class. Only the highest level `L4` is and should be used by other passes!
    - `StructuralSignalExpr.py` generates the IR of a signal expression (e.g. `s.in_[2].bar[0:4]`).
    - The user should only use passes exposed through the top level `__init__.py`. Other passes are used only for
    framework testing purposes.
