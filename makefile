run-dev:
	docker-compose up --build -d

cli:
	docker-compose exec app sh
