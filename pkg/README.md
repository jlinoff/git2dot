## Package for use in a virtual environment

Shows how to package git2dot into a python package for
distribution using a virtual environment. When the installation
is complete, you will be able to run git2dot as a python package
from a local virtual environment.

> This is not meant to be a guide to doing an official distribution.
> To do that you will want to use wheels.
> Please see http://pythonwheels.com/ for details.

It works by creating a setup.py distutils script that packages
the contents of a local git2dot package into a module in the
local virtual environment so that it can be run as follows:

```bash
$ . venv/bin/activate
(venv)$ python git2dot -h
(venv)$ deactivate
$
```

Here is how you set it up in the local venv virtualenv.

```bash
$ make
```

It will create the following package related files:

1. ``setup.py``
2. ``git2dot/__init__.py``
3. ``git2dot/__main.py``

It will also create a local virtual environment in ``venv``.

You may need to tweak the PYTHON and VIRTUALENV variables
in the Makefile for your environment.

You can use this as template for installing any program or
library into your environment.
