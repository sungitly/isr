.PHONY: npm-install build-res clean-pyc pip-install upgrade-db run-all

.DEFAULT_GOAL := build-all

npm-install:
	npm install

build-res:
	grunt --force

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

pip-install:
	pip install -r requirements.txt

upgrade-db:
	python manage.py db upgrade

build-all:npm-install build-res clean-pyc pip-install upgrade-db

run-server:
	python manage.py runserver

run-all: npm-install build-res clean-pyc pip-install upgrade-db run-server