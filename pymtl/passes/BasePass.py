#=========================================================================
# BasePass.py
#=========================================================================
# An "abstract" base class for all passes.
#
# Author : Shunning Jiang
# Date   : Dec 17, 2017

class BasePass(object):

  def __init__( self, debug=False ): # initialize parameters
    self.debug = debug

  def apply( self, m ): # execute pass on model m
    pass
