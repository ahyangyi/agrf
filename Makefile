.PHONY: doc clean test

doc:
	python tools/docgen.py
	cd docs && $(MAKE) html

update-images:
	python tools/update-images.py

clean:
	cd docs && $(MAKE) clean

test:
	pytest

.DEFAULT_GOAL := test
