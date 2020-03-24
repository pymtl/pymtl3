Bits Hardware Data Type
=======================

Semantics
---------

This section defines the expected behavior of different operations
on Bits objects and Python ``int`` objects.

- General principles
  + The bitwidth of ``int`` objects is inferred to be the minimal number of bits required to hold its value.
  + Implicit truncation is not allowed.
  + Implicit zero extension is allowed and will be attempted in cases of bitwidth mismatch.
  + Currently all operations of bits and integers preserve the unsigned semantics.

Following the above principles, 

Bitwidth rules
^^^^^^^^^^^^^^

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
   * - i^~j
     - i^~j
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
-------------------------

We recommend not using Python ``and`` and ``or`` operators on Bits/``int``
objects because they carry special Python semantics which is not compliant
with the PyMTL semantics. Use ``&`` and ``|`` instead.

.. autoclass:: pymtl3.datatypes.PythonBits.Bits
   :members:
   :special-members:
   :private-members:
   :undoc-members:
