#!/usr/bin/env python
import os
import sys
from shutil import rmtree

from setuptools import setup, Command

NAME = 'palpao_server'
DESCRIPTION = 'ALPAO, Boston MEMS, Physik Instrument Deformable mirrors interface'
URL = 'https://github.com/lbusoni/palpao_server'
EMAIL = 'lorenzo.busoni@inaf.it'
AUTHOR = 'Lorenzo Busoni'
LICENSE= 'MIT'
KEYWORDS= 'plico, deformable mirror, ALPAO, Boston MEMS, Physik Instrument, piezo, laboratory, instrumentation control',


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
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        self.status('Pushing git tags…')
        os.system('git tag v{0}'.format(about['__version__']))
        os.system('git push --tags')

        sys.exit()


setup(name=NAME,
      description=DESCRIPTION,
      version=about['__version__'],
      classifiers=['Development Status :: 4 - Beta',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6',
                   ],
      long_description=open('README.md').read(),
      url=URL,
      author_email=EMAIL,
      author=AUTHOR,
      license=LICENSE,
      keywords=KEYWORDS,
      packages=['palpao_server',
                'palpao_server.mirror_controller',
                'palpao_server.process_monitor',
                'palpao_server.scripts',
                'palpao_server.utils',
                ],
      entry_points={
          'console_scripts': [
              'palpao_mirror_controller_1=palpao_server.scripts.palpao_mirror_controller_1:main',
              'palpao_mirror_controller_2=palpao_server.scripts.palpao_mirror_controller_2:main',
              'palpao_kill_all=palpao_server.scripts.palpao_kill_processes:main',
              'palpao_start=palpao_server.scripts.palpao_process_monitor:main',
              'palpao_stop=palpao_server.scripts.palpao_stop:main',
          ],
      },
      package_data={
          'palpao_server': ['conf/palpao_server.conf', 'calib/*'],
      },
      install_requires=["plico>=0.15",
                        "palpao>=0.16",
                        "numpy",
                        "scipy",
                        "psutil",
                        "six",
                        "pyfits",
                        "pi_gcs",
                        ],
      include_package_data=True,
      test_suite='test',
      cmdclass={'upload': UploadCommand, },
      )
