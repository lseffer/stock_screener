
run: 
	@echo 'Starting containers...'
	@docker-compose up -d

test: 
	@echo 'Running tests...'
	@docker-compose run \
	  --rm \
	  --no-deps \
	  --entrypoint='' \
	  worker \
	  python -m unittest discover tests/ \
	  && mypy --config-file tests/mypy.ini utils/
