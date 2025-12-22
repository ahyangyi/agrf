.PHONY: doc clean test

doc:
	cd docs && $(MAKE) html

clean:
	cd docs && $(MAKE) clean

test:
	pytest

.DEFAULT_GOAL := test
