#=========================================================================
# errors.py
#=========================================================================
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Jan 4, 2019

class VerilatorCompileError( Exception ):
	""" Compiling error for verilator """
	def __init__( self, err ):
		return super( VerilatorCompileError, self ).__init__( \
    "Verilator compilation error: {}".format( err ) )

class PyMTLImportError( Exception ):
  """ Raise error when import goes wrong """
  def __init__( self, model_name, err ):
    return super( PyMTLImportError, self ).__init__( \
    "Error while importing instance of {}: {}".format( model_name, err ) )
