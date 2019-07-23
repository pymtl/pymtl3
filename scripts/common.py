#=========================================================================
# common
#=========================================================================

import os
import string
import subprocess
import sys

#-------------------------------------------------------------------------
# String interpolation
#-------------------------------------------------------------------------

def S( s ):
  frame = sys._getframe(1)
  template = string.Template(s)
  return template.substitute(**frame.f_locals)

#-------------------------------------------------------------------------
# Assemble path
#-------------------------------------------------------------------------

def P( *args ):
  return os.path.join( *args )

#-------------------------------------------------------------------------
# Run command with string interpolation
#-------------------------------------------------------------------------

def run( cmd ):
  frame = sys._getframe(1)
  template = string.Template(cmd)
  cmd_ = template.substitute(**frame.f_locals)
  vprint( " - run:", cmd_ )

  try:

    result = subprocess.check_output( cmd_, shell=True ).strip()

  except subprocess.CalledProcessError as e:
    print "\n ERROR: running the following command\n {} \n".format( ' '.join(e.cmd) )
    print e.output
    exit(1)

  print result
  return result

#-------------------------------------------------------------------------
# Quiet run
#-------------------------------------------------------------------------

def runq( cmd ):
  frame = sys._getframe(1)
  template = string.Template(cmd)
  cmd_ = template.substitute(**frame.f_locals)
  vprint( " - run:", cmd_ )

  try:

    result = subprocess.check_output( cmd_, shell=True ).strip()

  except subprocess.CalledProcessError as e:
    print "\n ERROR: running command \n"
    print e.cmd
    print e.output
    exit(1)

  return result

#-------------------------------------------------------------------------
# Run and return exit status
#-------------------------------------------------------------------------

def run_test( cmd ):
  frame = sys._getframe(1)
  template = string.Template(cmd)
  cmd_ = template.substitute(**frame.f_locals)
  vprint( " - run test:", cmd_ )
  return subprocess.call( cmd_, shell=True )

#-------------------------------------------------------------------------
# Verbose print
#-------------------------------------------------------------------------

verbose = False
def vprint( msg, value=None ):
  if verbose:
    if value != None:
      print msg, value
    else:
      print msg
