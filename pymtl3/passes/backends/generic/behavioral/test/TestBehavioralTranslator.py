#=========================================================================
# TestBehavioralTranslator.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Provide a behavioral translator that fits testing purposes."""

from pymtl3.passes.backends.generic.behavioral import BehavioralTranslator


def mk_TestBehavioralTranslator( _BehavioralTranslator ):
  def make_indent( src, nindent ):
    """Add nindent indention to every line in src."""
    indent = '  '
    for idx, s in enumerate( src ):
      src[ idx ] = nindent * indent + s

  class TestBehavioralTranslator( _BehavioralTranslator ):
    """Testing translator that implements behavioral callback methods."""

    def rtlir_data_type_translation( s, m, dtype ):
      """Translate `dtype` in component `m`.

      This method should be implemented by the structural translator. Since
      we are doing unit testing of the behavioral translator, I added it here
      so everything will work. This method does conflict with the actual
      implementation of `rtlir_data_type_translation` when we start testing
      RTLIRTranslator. My current solution is to explicitly check for the
      test translator's name and if it's a match then call the actual
      implementation.
      """
      if s.__class__.__name__ == 'TestRTLIRTranslator':
        return super(). \
          rtlir_data_type_translation( m, dtype )
      else:
        return str(dtype)

    def rtlir_tr_upblk_decls( s, upblk_decls ):
      decls = ''
      for upblk_decl in sorted(upblk_decls, key=lambda x: x[0]):
        make_indent( upblk_decl, 1 )
        decls += '\n' + '\n'.join( upblk_decl )
      return f'upblk_decls:{decls}\n'

    def rtlir_tr_upblk_decl( s, upblk, src, py_src ):
      return [f'upblk_decl: {upblk.__name__}']

    def rtlir_tr_upblk_py_srcs( s, upblk_py_srcs ):
      py_srcs = ''
      for upblk_py_src in sorted(upblk_py_srcs, key=lambda x: x[0]):
        make_indent( upblk_py_src, 1 )
        py_srcs += '\n' + '\n'.join( upblk_py_src )
      return f'upblk_py_srcs:{py_srcs}\n'

    def rtlir_tr_upblk_py_src( s, upblk, is_lambda, src, lino, filename ):
      return [f'upblk_py_src: {upblk.__name__}']

    def rtlir_tr_upblk_srcs( s, upblk_srcs ):
      srcs = ''
      for upblk_src in sorted(upblk_srcs, key=lambda x: x[0]):
        make_indent( upblk_src, 1 )
        srcs += '\n' + '\n'.join( upblk_src )
      return f'upblk_srcs:{srcs}\n'

    def rtlir_tr_upblk_src( m, upblk, rtlir_upblk ):
      return [f'upblk_src: {rtlir_upblk.name}']

    def rtlir_tr_behavioral_freevars( s, freevars ):
      srcs = ''
      for freevar in sorted(freevars, key=lambda x: x[0]):
        make_indent( freevar, 1 )
        srcs += '\n' + '\n'.join( freevar )
      return f'freevars:{srcs}\n'

    def rtlir_tr_behavioral_freevar( s, id_, rtype, array_type, dtype, obj ):
      return [f'freevar: {id_}']

    def rtlir_tr_behavioral_tmpvars( s, tmpvars ):
      srcs = ''
      for tmpvar in sorted(tmpvars, key=lambda x: x[0]):
        make_indent( tmpvar, 1 )
        srcs += '\n' + '\n'.join( tmpvar )
      return f'tmpvars:{srcs}\n'

    def rtlir_tr_behavioral_tmpvar( s, id_, upblk_id, dtype ):
      return [f'tmpvar: {id_} in {upblk_id} of {dtype}']

    def rtlir_tr_unpacked_array_type( s, array_rtype ):
      """Translate unpacked array type.

      This method should be implemented by the structural translator. Since
      we are doing unit testing of the behavioral translator, I added it here
      so everything will work. To avoid conflicting with the actual implementation
      of `rtlir_tr_unpacked_array_type`, this method returns different values
      depending on the name of the class (i.e. whether we are doing unit testing
      of the behavioral translator or the RTLIR translator).
      """
      if s.__class__.__name__ == 'TestRTLIRTranslator':
        return "" if array_rtype is None else repr(array_rtype)
      else:
        return f'unpacked_array: {array_rtype}'

    def rtlir_tr_vector_dtype( s, dtype ):
      """Translate vector data type.

      This method should be implemented by the structural translator. Since
      we are doing unit testing of the behavioral translator, I added it here
      so everything will work. To avoid conflicting with the actual implementation
      of `rtlir_tr_vector_dtype`, this method returns different values
      depending on the name of the class (i.e. whether we are doing unit testing
      of the behavioral translator or the RTLIR translator).
      """
      if s.__class__.__name__ == 'TestRTLIRTranslator':
        return str( dtype )
      else:
        return f'vector: {dtype}'

  return TestBehavioralTranslator

TestBehavioralTranslator = mk_TestBehavioralTranslator( BehavioralTranslator )
