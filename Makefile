PYTHON ?= /usr/bin/env python3
all: hazmat_merged
hazmat_merged: hazmat/*.py hazmat/*/*.py 
	zip --quiet hazmat hazmat/*.py hazmat/*/*.py
	zip --quiet --junk-path hazmat hazmat/__main__.py
	echo '#!$(PYTHON)' > hazmat_merged
	cat hazmat.zip >> hazmat_merged
	rm hazmat.zip
	chmod a+x hazmat_merged
