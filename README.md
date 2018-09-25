# PALPAO SERVER: deformable mirror controller 

This is part a component of the Plico framework to control DMs (Alpao, MEMS)


## Installation

### Installing

From the wheel

```
pip install palpao_server-XXX.whl
```

In palpao source dir

```
pip install .
```

During development you want to update use

```
pip install -e .
```
that install a python egg with symlinks to the source directory in such 
a way that chages in the python code are immediately available without 
the need for re-installing (beware of conf/calib files!)

### Uninstall

```
pip uninstall palpao_server
```

### Config files

The application uses `appdirs` to locate configurations, calibrations 
and log folders: the path varies as it is OS specific. 
The configuration files are copied when the application is first used
from their original location in the python package to the final
destination, where they are supposed to be modified by the user.
The application never touches an installed file (no delete, no overwriting)

To query the system for config file location, in a python shell:

```
import palpao_server
palpao_server.defaultConfigFilePath
```


The user can specify customized conf/calib/log file path for both
servers and client (how? ask!)


## Usage

### Starting Server

```
palpao_start
```
Starts the 2 servers that control one device each.


### Using client 

See palpao


### Stopping Palpao

To kill the servers

```
palpao_stop
```

More hard:

```
palpao_kill_all
```


## Administration Tool

For developers.


### Testing
Never commit before tests are OK!
To run the unittest and integration test suite execute in palpao source dir

```
python setup.py test
```


### Creating a Conda environment
Use the Anaconda GUI or in terminal

```
conda create --name palpao 
```

To create an environment with a specific python version

```
conda create --name palpao26  python=2.6
```


It is better to install available packages from conda instead of pip. 

```
conda install --name palpao matplotlib scipy ipython numpy
```

### Packaging and distributing

See https://packaging.python.org/tutorials/distributing-packages/#

To make a source distribution

```
python setup.py sdist
```

and the tar.gz is created in palpao/dist


If it is pure Python and works on 2 and 3 you can make a universal wheel 

```
python setup.py bdist_wheel --universal
```

Otherwise do a pure wheel

```
python setup.py bdist_wheel
```

The wheels are created in palpao/dist. I suppose one can trash palpao/build now and distribute the files in palpao/dist


To upload on pip (but do you really want to make it public?)

```
twine upload dist/*
```