# This Makefile creates the git2dot executable python module in a
# local virtual environment named: venv.
#
# It works by creating a setup.py distutils script that packages
# the contents of a local git2dot package into a module in the
# local virtual environment so that it can be run as follows:
#
#    $ . venv/bin/activate
#    (venv)$ python git2dot -h
#    (venv)$ deactivate
#
# To setup the environment:
#
#    $ make
#
# The git2dot script is simply copied from the top level
# directory into the local git2dot package directory.
#
# The clean target cleans up everything.
#
# To use it in your local environment, change the PYTHON and
# VIRTUALENV variables.
PYTHON     := python2.7
VIRTUALENV := virtualenv-2.7
VENV       := venv
FILES      := git2dot \
		git2dot/__init__.py \
		git2dot/__main__.py \
		git2dot/git2dot.py \
		setup.py

.PHONY: all clean

all: $(FILES) $(VENV) $(venv)/lib/$(PYTHON)/site-packages/git2dot
	. $(VENV)/bin/activate ; \
	$(PYTHON) git2dot -h ; \
	$(PYTHON) git2dot --version

# Clean up everything to guarantee that this process is idempotent.
clean:
	find . -type f -name '*~' -delete
	rm -rf git2dot venv setup.py build

# Install git2dot.
$(venv)/lib/$(PYTHON)/site-packages/git2dot: $(FILES) $(VENV)
	. $(VENV)/bin/activate ; \
	which $(PYTHON) ; \
	pip install python-dateutil ; \
	$(PYTHON) setup.py install

# Create the directory.
git2dot: ; mkdir $@

# Create an empty __init__.py.
git2dot/__init__.py: ; touch $@

# Create __main__.py so that python knows how to execute this module.
git2dot/__main__.py:
	echo 'from git2dot import main' > $@
	echo 'main()' >> $@
	chmod a+x $@

# Use the official version of git2dot.py.
git2dot/git2dot.py: ../git2dot.py
	cp $< $@

# Create the setup.py that is used to install the module.
# Note that the version is not explicitly specified.
# For a production release, it should be.
setup.py:
	echo 'from distutils.core import setup' >$@
	echo "setup(name='git2dot'," >>$@
	echo "      description='Visualize a git repository.'," >>$@
	echo "      license='MIT Open Source'," >>$@
	echo "      url='https://github.com/jlinoff/git2dot'," >>$@
	echo "      packages=['git2dot']," >>$@
	echo "     )" >> $@

$(VENV): ; $(VIRTUALENV) $@


