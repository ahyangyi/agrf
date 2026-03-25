.PHONY: doc clean test

doc:
	python tools/docgen.py
	cd docs && $(MAKE) html

clean:
	cd docs && $(MAKE) clean

test:
	pytest

.DEFAULT_GOAL := test
