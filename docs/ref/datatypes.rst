Hardware Data Types
===================

Bits Type
---------

Semantics
^^^^^^^^^

This section defines the expected behavior of different operations
on Bits objects and Python ``int`` objects.

Here are the general principles of Bits/``int`` operation semantics:

- Implicit truncation is not allowed.
- Implicit zero extension is allowed and will be attempted in cases of bitwidth mismatch.
- Currently all operations of bits and integers preserve the unsigned semantics.

Following the above principles, here is how to determine the bitwidth of an expression:

- A ``BitsN`` object has an explicit bitwidth of ``N``.
- An ``int`` object has an inferred bitwidth of the minimal number of bits required to hold its value.
- For binary operations that are not ``<<`` and ``>>``

  - If both sides have explicit bitwidth

    - it is an error if bitwidth of both sides mismatch.
    - the result has an explicit bitwidth indicated in the operation bitwidth rule table.

  - If both sides have inferred bitwidth

    - the shorter side will be zero-extended to have the same bitwidth as the longer side.
    - the result has an inferred bitwidth indicated in the operation bitwidth rule table.

  - If one side has explicit bitwidth and the other has inferred bitwidth

    - it is an error if the inferred bitwidth is smaller than the explicit bitwidth.
    - otherwise, a zero extension on the inferred side to the explicit bitwidth is attempted.
    - the result has an explicit bitwidth indicated in the operation bitwidth rule table.
- For binary operations ``<<`` and ``>>``

  - The bitwidth of the right hand side is ignored.
  - If the left hand side has explicit bitwidth, then the result has an explicit bitwidth indicated in the operation bitwidth rule table.
  - If the left hand side has inferred bitwidth, then the result has an inferred bitwidth indicated in the operation bitwidth rule table.

- For unary operations

  - If the operand has explicit bitwidth, then the result has an explicit bitwidth indicated in the operation bitwidth rule table.
  - If the operand has inferred bitwidth, then the result has an inferred bitwidth indicated in the operation bitwidth rule table.

Opeartion bitwidth rules
^^^^^^^^^^^^^^^^^^^^^^^^

Assuming the bitwidth of Bits or integer objects ``i``, ``j``, and ``k`` are ``n``,
``m``, and ``p``, respectively. The following table defines the result of different
operations. Note that the Verilog rules only apply to self-determined expressions.

.. list-table:: PyMTL3 and Verilog Bitwidth Rules
   :header-rows: 1

   * - PyMTL Expression
     - Verilog Expression
     - PyMTL3
     - Verilog
   * - i+j
     - i+j
     - max(n, m)
     - max(n, m)
   * - i-j
     - i-j
     - max(n, m)
     - max(n, m)
   * - i*j
     - i*j
     - max(n, m)
     - max(n, m)
   * - i/j
     - i/j
     - max(n, m)
     - max(n, m)
   * - i%j
     - i%j
     - max(n, m)
     - max(n, m)
   * - i&j
     - i&j
     - max(n, m)
     - max(n, m)
   * - i|j
     - i|j
     - max(n, m)
     - max(n, m)
   * - i^j
     - i^j
     - max(n, m)
     - max(n, m)
   * - ~i
     - ~i
     - n
     - n
   * - i>>j
     - i>>j
     - n
     - n
   * - i<<j
     - i<<j
     - n
     - n
   * - i==j
     - i==j
     - 1
     - 1
   * - i and j
     - i&&j
     - max(n, m)
     - 1
   * - i or j
     - i||j
     - max(n, m)
     - 1
   * - i>j
     - i>j
     - 1
     - 1
   * - i>=j
     - i>=j
     - 1
     - 1
   * - i<j
     - i<j
     - 1
     - 1
   * - i<=j
     - i<=j
     - 1
     - 1
   * - reduce_and(i)
     - &i
     - 1
     - 1
   * - reduce_or(i)
     - \|i
     - 1
     - 1
   * - reduce_xor(i)
     - ^i
     - 1
     - 1
   * - j if i else k
     - i?j:k
     - m where m == p
     - max(m, p)
   * - conat(i,..,j)
     - {i,...,j}
     - n + ... + m
     - n + ... + m
   * - i[j]
     - i[j]
     - 1
     - 1
   * - i[j:k]
     - i[j:k]
     - k-j
     - k-j


Supported Bits opeartions
^^^^^^^^^^^^^^^^^^^^^^^^^

We recommend not using Python ``and`` and ``or`` operators on Bits/``int``
objects because they carry special Python semantics which is not compliant
with the PyMTL semantics. Use ``&`` and ``|`` instead.

.. autoclass:: pymtl3.datatypes.PythonBits.Bits
   :members:
   :special-members:
   :private-members:
   :undoc-members:

BitStruct Type
--------------

To be added...
