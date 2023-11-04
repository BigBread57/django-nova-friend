ready:
	poetry run python ./src/changeme/changeme.py

poetry_check:
	poetry check

pip_check:
	pip check

dotenv:
	dotenv-linter config/.env config/.env.template

all_style:
	flake8 . --format=nova
	python manage.py check --fail-level ERROR
	python manage.py makemigrations --dry-run --check
	python manage.py lintmigrations --exclude-apps=axes --exclude-apps=sites \
		--warnings-as-errors
	poetry check

check:
	make types
	make style

django_check:
	DATABASE_URL=postgres://postgres@db/postgres docker-compose run web python manage.py check  --fail-level WARNING

django_staticfiles:
	DJANGO_ENV=production DJANGO_COLLECTSTATIC_DRYRUN=1 python \
	manage.py collectstatic --no-input --dry-run

django_makemigrations:
	python manage.py makemigrations --dry-run --check

yaml:
	yamllint -d '{"extends": "default", "ignore": ".venv" }' -s .

PO_lint:
	polint -i location,unsorted locale

ci_types:
	ci-types ci-style ci-check ci-django-check ci-yaml

flake8:
	flake8 .

mypy:
	mypy manage.py src $(find tests -name '*.py')

django_lintmigrations:
	python manage.py lintmigrations --include-apps=nova_friend \
	--warnings-as-errors

pytest_coverage:
	pytest --cov=src --cov-branch --cov-report html

pytest:
	pytest --dead-fixtures \
    && coverage run -m pytest --junitxml=report.xml \
    && coverage xml