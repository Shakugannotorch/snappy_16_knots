long_description ="""\ 
This package provides a database of 16 crossing knots for use
with the spherogram and snappy packages.
"""

import re, sys, subprocess, os, shutil, glob
import requests
from setuptools import setup, Command
from setuptools.command.build_py import build_py

sqlite_files = ['16_knots.sqlite']

pattern = ('version https://git-lfs.github.com/spec/v1\n'
           'oid sha256:([a-z0-9]+)\n'
           'size ([0-9]+)')

def get_lfs_file_url(user, repo, object_id, size):
    """
    Use the GitHub API to get URL to a LFS file.  The URL is dynamic and
    is good for an hour or so.
    """
    url = f'https://github.com/{user}/{repo}.git/info/lfs/objects/batch'
    body = {'operation': 'download',
            'transfer': ['basic'],
            'objects': [{'oid': object_id, 'size': size}]}
    headers = {'Accept':'application/vnd.git-lfs+json',
               'Content-Type': 'application/json'}
    response = requests.post(url, json=body, headers=headers)
    if response.status_code != 200:
        raise ConnectionError('Could not get download URL from GitHub')
    data = response.json()['objects'][0]
    assert data['oid'] == object_id
    return data['actions']['download']['href']


def download_as_file(url, path):
    """
    Based on https://stackoverflow.com/questions/16694907/
    """
    with requests.get(url, stream=True) as response:
        with open(path, 'wb') as file:
            shutil.copyfileobj(response.raw, file)


def fetch_if_needed(path):
    if os.path.getsize(path) < 1000:
        with open(path) as file:
            match = re.match(pattern, file.read())
            if match:
                oid, length = match.groups()
                length = int(length)
                url = get_lfs_file_url('Shakugannotorch', 'snappy_16_knots', oid, length)
                os.rename(path, path + '.orig')
                print(f'Fetching data file {os.path.basename(path)}...',
                      end='', flush=True)
                download_as_file(url, path)
                if int(length) != os.path.getsize(path):
                    raise ConnectionError('Download was wrong size.')
                size = length/(1024**2)
                print(f' Successfully retrieved {size:.1f}M')

            
# --- end git lfs file stuff 

def check_call(args):
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError:
        executable = args[0]
        command = [a for a in args if not a.startswith('-')][-1]
        raise RuntimeError(command + ' failed for ' + executable)


class Clean(Command):
    """
    Removes the usual build/dist/egg-info directories as well as the
    sqlite database files.
    """
    user_options = []
    def initialize_options(self):
        pass 
    def finalize_options(self):
        pass
    def run(self):
        for dir in ['build', 'dist'] + glob.glob('*.egg-info'):
            if os.path.exists(dir):
                shutil.rmtree(dir)
        for file in glob.glob('manifold_src/*.sqlite'):
            os.remove(file)


class BuildPy(build_py):
    """
    Rebuilds the sqlite database files if needed.
    """
    def initialize_options(self):
        build_py.initialize_options(self)
        os.chdir('manifold_src')
        csv_source_files = glob.glob(
            os.path.join('original_manifold_sources', '*.csv*'))
        # When there are no csv files, we are in an sdist tarball
        if len(csv_source_files) == 0:
            fetch_if_needed('plausible_knots.sqlite')
        else:
            print('Rebuilding stale sqlite databases from csv sources if necessary...')
            check_call([sys.executable, 'make_sqlite_db.py'])
        os.chdir('..')

class Release(Command):
    user_options = [('install', 'i', 'install the release into each Python')]
    def initialize_options(self):
        self.install = False
    def finalize_options(self):
        pass
    def run(self):
        pythons = os.environ.get('RELEASE_PYTHONS', sys.executable).split(',')
        check_call([pythons[0], 'setup.py', 'clean'])
        check_call([pythons[0], 'setup.py', 'bdist_wheel', '--universal'])
        check_call([pythons[0], 'setup.py', 'sdist'])
        if self.install:
            for python in pythons:
                check_call([python, 'setup.py', 'pip_install', '--no-build-wheel'])


class PipInstall(Command):
    user_options = [('no-build-wheel', 'n', 'assume wheel has already been built')]
    def initialize_options(self):
        self.no_build_wheel = False
    def finalize_options(self):
        pass
    def run(self): 
        python = sys.executable
        check_call([python, 'setup.py', 'build'])
        if not self.no_build_wheel:
            check_call([python, 'setup.py', 'bdist_wheel', '--universal'])
        egginfo = 'snappy_16_knots.egg-info'
        if os.path.exists(egginfo):
            shutil.rmtree(egginfo)
        wheels = glob.glob('dist' + os.sep + '*.whl')
        new_wheel = max(wheels, key=os.path.getmtime)            
        check_call([python, '-m', 'pip', 'install', '--upgrade',
                    '--upgrade-strategy', 'only-if-needed',
                    new_wheel])

class Test(Command):
    user_options = []
    def initialize_options(self):
        pass 
    def finalize_options(self):
        pass
    def run(self):
        build_lib_dir = os.path.join('build', 'lib')
        sys.path.insert(0, build_lib_dir)
        from snappy_16_knots.test import run_tests
        sys.exit(run_tests())

# Get version number from module
version = re.search("__version__ = '(.*)'",
                    open('python_src/__init__.py').read()).group(1)

setup(
    name = 'snappy_16_knots',
    version = version,
    long_description = long_description,
    author = 'Marc Culler and Nathan M. Dunfield and Mattias Goerner and Shana Li and Malik Obeidin',
    author_email = 'snappy-help@computop.org',
    license='GPLv2+',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: OS Independent',
        'Programming Language :: C',
        'Programming Language :: Cython',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Mathematics',
        ],
    install_requires = ['snappy_15_knots'],
    packages = ['snappy_16_knots', 'snappy_16_knots/sqlite_files'],
    package_dir = {'snappy_16_knots':'python_src',
                   'snappy_16_knots/sqlite_files':'manifold_src'},
    package_data = {'snappy_16_knots/sqlite_files': sqlite_files},
    ext_modules = [],
    zip_safe = False,
    cmdclass = {'release': Release,
                'build_py': BuildPy,
                'clean': Clean,
                'pip_install':PipInstall,
                'test':Test
    },
)

