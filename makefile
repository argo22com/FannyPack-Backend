run-dev:
	docker-compose up --build -d

cli:
	docker-compose exec app sh

migrate:
	docker-compose exec app sh -c "python manage.py migrate"
