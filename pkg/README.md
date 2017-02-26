Shows how to package git2dot into a python package for official
distribution using a virtual environment. When the installation
is complete, you will be able to run git2dot as a python package
from a local virtual environment.

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

You can use this as template for installing any program or
library into your environment.

