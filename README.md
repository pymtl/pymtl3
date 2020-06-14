PyMTL 3 (Mamba)
==========================================================================

[![Build Status](https://travis-ci.com/pymtl/pymtl3.svg?branch=master)](https://travis-ci.com/pymtl/pymtl3)
[![Documentation Status](https://readthedocs.org/projects/pymtl3/badge/?version=latest)](https://pymtl3.readthedocs.io/en/latest/?badge=latest)
[![Codecov Status](https://codecov.io/gh/pymtl/pymtl3/branch/master/graph/badge.svg)](https://codecov.io/gh/pymtl/pymtl3)

PyMTL 3 (Mamba) is the latest version of PyMTL, an open-source
Python-based hardware generation, simulation, and verification framework with
multi-level hardware modeling support. The original PyMTL was introduced
at MICRO-47 in December, 2014. Please note that PyMTL 3 is currently
**beta** software that is under active development and documentation is
currently quite sparse.

In June 2019, [Keeping Computer Hardware Fast and Furious: "PyMTL is a fantastic example of what we need to jump-start the open-source hardware ecosystem…It’s a key missing link."](https://research.cornell.edu/news-features/keeping-computer-hardware-fast-and-furious "Link to the article") was featured on Cornell Research.

User Forum
----------
We recommend the user to post on https://groups.google.com/forum/#!forum/pymtl-users to ask questions about using PyMTL 3. The github issues are reserved for development purposes, e.g., bug reports and feature requests.

Related publications
--------------------------------------------------------------------------

- Shunning Jiang, Christopher Torng, and Christopher Batten. _"An Open-Source Python-Based Hardware Generation, Simulation, and Verification Framework."_ First Workshop on Open-Source EDA Technology (WOSET'18) held in conjunction with ICCAD-37, Nov. 2018.

- Shunning Jiang, Berkin Ilbeyi, and Christopher Batten. _"Mamba: Closing the Performance Gap in Productive Hardware Development Frameworks."_ 55th ACM/IEEE Design Automation Conf. (DAC-55), June 2018. 

- Derek Lockhart, Gary Zibrat, and Christopher Batten. _"PyMTL: A Unified Framework for Vertically Integrated Computer Architecture Research."_ 47th ACM/IEEE Int'l Symp. on Microarchitecture (MICRO-47), Dec. 2014.

License
--------------------------------------------------------------------------

PyMTL is offered under the terms of the Open Source Initiative BSD
3-Clause License. More information about this license can be found here:

  - http://choosealicense.com/licenses/bsd-3-clause
  - http://opensource.org/licenses/BSD-3-Clause
  
Installation
------------

The steps for installing these prerequisites and PyMTL on a fresh Ubuntu
distribution are shown below. They have been tested with Ubuntu Xenial 18.04.

### Install PyMTL 3


**tl; dr** ```pip install pymtl3```

----

PyMTL 3 requires Python 3.6+. We highly recommend you work inside a **virtual environment** instead of calling ```sudo pip install```. Starting from Python 3.5, the use of venv is now recommended for creating virtual environments.

```
 $ cd <path to where venvs are stored>
 $ python3 -m venv pymtl3 # you can use whatever Python 3.6+ binary you have
 $ source pymtl3/bin/activate
```
PyMTL 3 needs to use cffi, so install these packages first.

```
 $ sudo apt-get install git python-dev libffi-dev
```

PyMTL 3 is available on pypi.org. As a result, you are able to just call ```pip install pymtl3``` to install PyMTL 3.

```
 $ pip install pymtl3
```

When you relaunch the bash session, you need to re-enable the venv.

```
 $ source <path to where venvs are stored>/pymtl3/bin/activate
```

When you're done testing/developing but you don't want to close the terminal, you can deactivate the virtualenv:

```
 $ deactivate
```


Additional dependencies include ```verilator```(and ```pkg-config```) when you want to integrate SystemVerilog blackbox into your PyMTL simulation.

### Install Verilator

[Verilator](http://www.veripool.org/wiki/verilator) is an open-source toolchain for compiling SystemVerilog RTL
models into C++ simulators. You can install Verilator using the
standard package manager but the version available in the package
repositories is several years old. This means you will need to build and
install Verilator from source using the following commands:

```
 $ sudo apt-get install git make autoconf g++ libfl-dev bison
 $ mkdir -p ${HOME}/src
 $ cd ${HOME}/src
 $ wget http://www.veripool.org/ftp/verilator-4.036.tgz
 $ tar -xzvf verilator-4.036.tgz
 $ cd verilator-4.036
 $ ./configure
 $ make
 $ sudo make install
```

Verify that Verilator is on your path as follows:

```
 $ cd $HOME
 $ which verilator
 $ verilator --version
```

PyMTL uses `pkg-config` to find the Verilator source files when
integrating SystemVerilog blackbox. Install
`pkg-config` and verify that it is setup correctly as follows:

```
 $ sudo apt-get install pkg-config
 $ pkg-config --print-variables verilator
```

If `pkg-config` cannot find information about verilator, then you can
also explicitly set the following special environment variable:

```
 $ export PYMTL_VERILATOR_INCLUDE_DIR="/usr/local/share/verilator/include"
```

