install:
	poetry install

build:
	poetry build

package-install:
	python3 -m pip install --user dist/*.whl

force-reinstall:
	python3 -m pip install --force-reinstall --user dist/*.whl

quick-install:
	python3 -m pip install .

test:
	poetry run pytest

test-coverage:
	poetry run pytest --cov-report term-missing --cov=page_loader --cov-report xml

lint:
	poetry run flake8 page_loader