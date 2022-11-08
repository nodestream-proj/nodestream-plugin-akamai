.PHONY: clean
clean: clean-pyc 

.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -rf {} +
	find . -name '*.pyo' -exec rm -rf {} +
	find . -name '*~' -exec rm -rf {} +
	find . -name '__pycache__' -exec rm -rf {} +

.PHONY: run
run: 
	poetry install
	poetry run python main.py
