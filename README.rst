The SnapPy manifold database for 16 crossings knots
==========================================================

This repository stores the manifold databases for 16 crossing
knots, and includes the source code for the Python module
:code:`snappy_16_knots` which packages them up for use in SnapPy and
Spherogram. 

To install this package, do::

  python -m pip install --upgrade --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ snappy_16_knots

or, if you are using SageMath::

  sage -pip install --upgrade --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ snappy_16_knots

A prerequisite for using :code:`snappy_16_knots` is :code:`snappy_15_knots`; the above command
should be able to automatically install :code:`snappy_15_knots`, if it is not readily installed.

To use this module with SnapPy, do::

  >>> import snappy, snappy_16_knots

The extended census can then be accessed via SnapPy's :code:`Manifold` class. 
For example::

  >>> m = snappy.Manifold('K16a101')
  >>> m.triangulation_isosig()
  'yLLLPLLAwMLzwQQLQcbehfiljimnonrqrsstuvwxxxdjqdgtehqxqajhfuajoffaacv_bacB'

  >>> m = snappy.Manifold('K16a101(2,3)')
  >>> m.triangulation_isosig()
  ''yLLLPLLAwMLzwQQLQcbehfiljimnonrqrsstuvwxxxdjqdgtehqxqajhfuajoffaacv_bacB(2,3)''

The iterator for all manifolds in this module, along with those in 
:code:`snappy_15_knots`, is :code:`snappy.HTLinkExteriors`. 
For example::

  >>> len(snappy.HTLinkExteriors)
  1822509

  >>> for M in snappy.HTLinkExteriors[-9:-6]: print(M, M.volume()) 
  K16n1008898(0,0) 22.8613896980723
  K16n1008899(0,0) 17.0540820108716
  K16n1008900(0,0) 16.9295548661239

  >>> for M in snappy.HTLinkExteriors(num_cusps=2)[-3:]: print(M, M.volume(), M.num_cusps())
  L14n40046(0,0)(0,0) 18.6813172532672 2
  L14n40047(0,0)(0,0) 14.8257607028697 2
  L14n40048(0,0)(0,0) 23.2884335333958 2

The raw source for the tables are in::
  
  manifold_src/original_manifold_sources

stored as plain text CSV files for the potential convenience of other
users. The triangulations themselves are stored in the "isosig" format
of Burton, as described in the appendix to `this paper
<http://arxiv.org/abs/1110.6080>`_ with an added "decoration" suffix
that describes the peripheral framing.
