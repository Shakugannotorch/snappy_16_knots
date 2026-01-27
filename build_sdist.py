"""
The sdist does not contain the CSV files with the manifold data
because these are much to big for pypi.  Instead, it contains their
GitHub LFS identifiers
"""

import os, sys, shutil, subprocess, glob

os.makedirs('build', exist_ok=True)
clone = 'build/sdist_clone'
if os.path.exists(clone):
    shutil.rmtree(clone)
subprocess.check_call(['git', 'clone', '.', 'build/sdist_clone'],
                      env={'GIT_LFS_SKIP_SMUDGE':'1'})
os.chdir(clone)
subprocess.check_call([sys.executable, 'setup.py', 'sdist'])
tarball = glob.glob('dist/snappy_16_knots*.tar.gz')[0]
print(f'\nSource tarball created as\n\n    {clone}/{tarball}')



