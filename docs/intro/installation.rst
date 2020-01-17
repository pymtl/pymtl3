.. Documentation on installation

Installation
============

Install the PyMTL3 Framework
----------------------------

PyMTL3 requires >= Python3.6. We highly recommend you work inside a virtual
environment. Starting from Python 3.5, the use of ``venv`` is now recommended
for creating virtual environments:

.. prompt:: bash $

    cd <path to venv location>
    python3 -m venv pymtl3
    source pymtl3/bin/activate

PyMTL3 depends on `cffi <https://cffi.readthedocs.io>`_ which requires the
following packages:

.. prompt:: bash $

    sudo apt-get install git python-dev libffi-dev

After installing the dependent packages, you can install :pypi:`the PyMTL3
framework <pymtl3>` from PyPI as:

.. prompt:: bash $

    pip install pymtl3

.. note:: Your virtual environment will be deactivated when your current terminal
    session is termindated. To re-activate your PyMTL3 virtual environment:

    .. prompt:: bash $

        source <path to venv location>/pymtl3/bin/activate

    and to manually deactivate your current virtual environment:

    .. prompt:: bash $

        deactivate

Install the Verilator Simulator
-------------------------------

PyMTL3 requires `Verilator <https://www.veripool.org/wiki/verilator>`_, an open-source
toolchain for compiling SystemVerilog RTL models into C++ simulators, to co-simulate
Verilog modules with PyMTL3 components. You can install Verilator
using the standard package manager but the version available in the package repositories
is several years old. This means you probably need to build and install Verilator from
source using the following commands:

.. prompt:: bash $

    sudo apt-get install git make autoconf g++ libfl-dev bison
    mkdir -p $HOME/src
    cd $HOME/src
    wget http://www.veripool.org/ftp/verilator-4.024.tgz
    tar -xzvf verilator-4.024.tgz
    cd verilator-4.024
    ./configure
    make
    sudo make install

Verify that Verilator is on your ``PATH`` as follows:

.. prompt:: bash $

    verilator --version

PyMTL3 uses ``pkg-config`` to find the Verilator source files when integrating
Verilog blackboxes. Install ``pkg-config`` and verify that it is setup correctly
as follows:

.. prompt:: bash $

    sudo apt-get install pkg-config
    pkg-config --print-variables verilator

If ``pkg-config`` cannot find information about verilator, then you can also
explicitly set the following special environment variable:

.. prompt:: bash $

    export PYMTL_VERILATOR_INCLUDE_DIR="/usr/local/share/verilator/include"
