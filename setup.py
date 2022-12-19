#!/usr/bin/env python
import os
import sys
from shutil import rmtree

from setuptools import setup, Command

NAME = 'plico_dm_server'
DESCRIPTION = 'ALPAO, Boston MEMS, Physik Instrument Deformable mirrors interface'
URL = 'https://github.com/ArcetriAdaptiveOptics/plico_dm_server'
EMAIL = 'lorenzo.busoni@inaf.it'
AUTHOR = 'Lorenzo Busoni'
LICENSE = 'MIT'
KEYWORDS = 'plico, deformable mirror, ALPAO, Boston MEMS, Physik Instrument, piezo, laboratory, instrumentation control',

here = os.path.abspath(os.path.dirname(__file__))
# Load the package's __version__.py module as a dictionary.
about = {}
with open(os.path.join(here, NAME, '__version__.py')) as f:
    exec(f.read(), about)


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds...')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution...')
        os.system(
            '{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine...')
        os.system('twine upload dist/*')

        self.status('Pushing git tags...')
        os.system('git tag v{0}'.format(about['__version__']))
        os.system('git push --tags')

        sys.exit()


setup(name=NAME,
      description=DESCRIPTION,
      version=about['__version__'],
      classifiers=['Development Status :: 4 - Beta',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 3',
                   ],
      long_description=open('README.md').read(),
      url=URL,
      author_email=EMAIL,
      author=AUTHOR,
      license=LICENSE,
      keywords=KEYWORDS,
      packages=['plico_dm_server',
                'plico_dm_server.controller',
                'plico_dm_server.process_monitor',
                'plico_dm_server.scripts',
                'plico_dm_server.utils',
                ],
      entry_points={
          'console_scripts': [
              'plico_dm_controller_1=plico_dm_server.scripts.plico_dm_controller_1:main',
              'plico_dm_controller_2=plico_dm_server.scripts.plico_dm_controller_2:main',
              'plico_dm_kill_all=plico_dm_server.scripts.plico_dm_kill_processes:main',
              'plico_dm_start=plico_dm_server.scripts.plico_dm_process_monitor:main',
              'plico_dm_stop=plico_dm_server.scripts.plico_dm_stop:main',
          ],
      },
      package_data={
          'plico_dm_server': ['conf/plico_dm_server.conf', 'calib/*'],
      },
      install_requires=["plico>=0.20",
                        "plico_dm>=1.0.0",
                        "numpy",
                        "scipy",
                        "psutil",
                        "six",
                        "pi_gcs",
                        "PIL",
                        ],
      include_package_data=True,
      test_suite='test',
      cmdclass={'upload': UploadCommand, },
      )
