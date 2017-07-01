install-archlinux:  ## Install needed packages with pacman
	hash python2 2>/dev/null || sudo pacman -S python2
	hash virtualenv 2>/dev/null || sudo pip install -U virtualenv
	hash pip2 2>/dev/null || sudo pacman -S python-pip
	[ -f /usr/include/fuse/fuse.h ] || sudo pacman -S fuse2


venv2.7: .venv2.7/bin/activate  ## Setup virtualenv with python2.7

.venv2.7/bin/activate: requirements.txt setup.py
	test -d .venv2.7 || virtualenv --python=python2.7 .venv2.7
	.venv2.7/bin/pip install -e .[dev,test]
	touch .venv2.7/bin/activate


test: test2.7  ## Run tests for all supported python versions

test2.7: clean venv2.7  ## Run tests with python2.7
	.venv2.7/bin/python -mpytest test/test_all.py


clean:  ## Remove temporary files
	find . -name '*.pyc' -delete
	rm -rf build dist *.egg-info test/testroot


help: ## This help
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	    | sort \
	    | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: test
