.PHONY: help install test lint format clean run build deploy

help:		## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:	## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

install-dev:	## Install development dependencies
	pip install -r requirements-dev.txt

test:		## Run tests
	pytest test_*.py -v

test-coverage:	## Run tests with coverage
	pytest test_*.py -v --cov=. --cov-report=html --cov-report=term

lint:		## Run linting
	flake8 .
	mypy .

format:		## Format code
	black .
	isort .

format-check:	## Check code formatting
	black --check .
	isort --check-only .

clean:		## Clean up generated files
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -rf __pycache__
	rm -rf ./**/__pycache__
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

run:		## Run the application
	uvicorn main:app --reload

run-prod:	## Run the application in production mode
	uvicorn main:app --host 0.0.0.0 --port 8000

docker-build:	## Build Docker image
	docker build -t agentic-coder-api .

docker-run:	## Run Docker container
	docker run -p 8000:8000 agentic-coder-api

docker-compose:	## Run with Docker Compose
	docker-compose up --build

init:		## Initialize the project
	cp .env.example .env
	make install-dev

check:		## Run all checks (format, lint, test)
	make format-check
	make lint
	make test

pre-commit:	## Run pre-commit hooks
	pre-commit run --all-files

setup-hooks:	## Setup git hooks
	pre-commit install

deploy-staging:	## Deploy to staging environment
	# Add your staging deployment commands here
	echo "Deploying to staging..."

deploy-prod:	## Deploy to production environment
	# Add your production deployment commands here
	echo "Deploying to production..."

reformat:	## Reformat the codebase
	black .
	isort .

update-deps:	## Update dependencies
	pip-compile requirements.in
	pip-compile requirements-dev.in

security-check:	## Run security checks
	bandit -r .

profile:	## Run performance profiling
	python -m cProfile -o profile.prof main.py

docs:		## Generate documentation
	# Add documentation generation commands here
	echo "Generating documentation..."

setup-dev:	## Setup development environment
	python -m venv venv
	. venv/bin/activate
	make install-dev
	make setup-hooks

upgrade-pip:	## Upgrade pip
	python -m pip install --upgrade pip