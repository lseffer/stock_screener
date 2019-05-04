.PHONY: run test

run: 
	@echo 'Starting containers...'
	@docker-compose up -d --build

test: 
	@echo 'Running tests...'
	@docker-compose run \
	  --rm \
	  --no-deps \
	  --entrypoint='' \
	  worker \
	  python -m unittest discover tests/ -v \
	  && mypy --config-file tests/mypy.ini utils/
