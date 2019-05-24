#=========================================================================
# TestBehavioralTranslator.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Provide a behavioral translator that fits testing purposes."""

from __future__ import absolute_import, division, print_function

from pymtl.passes.translator.behavioral import BehavioralTranslator


def mk_TestBehavioralTranslator( _BehavioralTranslator ):
  def make_indent( src, nindent ):
    """Add nindent indention to every line in src."""
    indent = '  '
    for idx, s in enumerate( src ):
      src[ idx ] = nindent * indent + s

  class TestBehavioralTranslator( _BehavioralTranslator ):
    def rtlir_data_type_translation( s, m, dtype ):
      if s.__class__.__name__ == 'TestRTLIRTranslator':
        return super(TestBehavioralTranslator, s). \
          rtlir_data_type_translation( m, dtype )
      else:
        return str(dtype)

    def rtlir_tr_upblk_decls( s, upblk_srcs ):
      srcs = ''
      for upblk_src in sorted(upblk_srcs, key=lambda x: x[0]):
        make_indent( upblk_src, 1 )
        srcs += '\n' + '\n'.join( upblk_src )
      return 'upblk_decls:{}\n'.format( srcs )

    def rtlir_tr_upblk_decl( m, upblk, rtlir_upblk ):
      return ['upblk_decl: {}'.format( rtlir_upblk.name )]

    def rtlir_tr_behavioral_freevars( s, freevars ):
      srcs = ''
      for freevar in sorted(freevars, key=lambda x: x[0]):
        make_indent( freevar, 1 )
        srcs += '\n' + '\n'.join( freevar )
      return 'freevars:{}\n'.format( srcs )

    def rtlir_tr_behavioral_freevar( s, id_, rtype, array_type, dtype, obj ):
      return ['freevar: {id_}'.format( **locals() )]

    def rtlir_tr_behavioral_tmpvars( s, tmpvars ):
      srcs = ''
      for tmpvar in sorted(tmpvars, key=lambda x: x[0]):
        make_indent( tmpvar, 1 )
        srcs += '\n' + '\n'.join( tmpvar )
      return 'tmpvars:{}\n'.format( srcs )

    def rtlir_tr_behavioral_tmpvar( s, id_, upblk_id, dtype ):
      return ['tmpvar: {id_} in {upblk_id} of {dtype}'.format( **locals() )]

    def rtlir_tr_unpacked_array_type( s, array_rtype ):
      if s.__class__.__name__ == 'TestRTLIRTranslator':
        return "" if array_rtype is None else repr(array_rtype)
      else:
        return 'unpacked_array: {}'.format( array_rtype )

    def rtlir_tr_vector_dtype( s, dtype ):
      if s.__class__.__name__ == 'TestRTLIRTranslator':
        return str( dtype )
      else:
        return 'vector: {}'.format( dtype )

  return TestBehavioralTranslator

TestBehavioralTranslator = mk_TestBehavioralTranslator( BehavioralTranslator )
