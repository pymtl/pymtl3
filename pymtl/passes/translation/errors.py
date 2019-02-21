#=========================================================================
# errors.py
#=========================================================================
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Jan 4, 2019

class TranslationError( Exception ):
  """ Raise when translation goes wrong """
  def __init__( self, blk, x ):
    return super( TranslationError, self ).__init__( \
    "Error while translating {}. {}".format( blk.__name__, x ) )
