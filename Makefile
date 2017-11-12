.PHONY: test import-abi

test:
	pytest --flake8

import-abi:
	npm install && \
	cp ../Sonar/build/*.abi abis/
