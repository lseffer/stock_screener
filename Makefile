.PHONY: run run_prod tests stop

run: 
	@echo 'Starting containers...'
	@docker-compose up -d --build

run_prod:
	@echo 'Starting containers...'
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

tests: 
	@echo 'Running tests...'
	@docker-compose run \
	  --rm \
	  --no-deps \
	  --entrypoint='' \
	  worker \
	  bash -c "python -m unittest discover tests/ -v \
	  && python -m mypy --config-file tests/mypy.ini utils/"

stop:
	@docker-compose down
