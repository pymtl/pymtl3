#=========================================================================
# errors.py
#=========================================================================
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Jan 4, 2019

class VerilatorCompilationError( Exception ):
	""" Compiling error for verilator """
	def __init__( self, model_name, err ):
		return super( VerilatorCompilationError, self ).__init__( \
    "Error while verilating {}:\n{}".format( model_name, err ) )

class PyMTLImportError( Exception ):
  """ Raise error when import goes wrong """
  def __init__( self, model_name, err ):
    return super( PyMTLImportError, self ).__init__( \
    "Error while importing instance of {}:\n{}".format( model_name, err ) )
