.PHONY: build up down logs run-welcome fmt

build:
	docker-compose build

up:
	docker-compose up --build

down:
	docker-compose down

logs:
	docker-compose logs -f

run-welcome:
	curl -X POST http://localhost:8000/run-welcome

fmt:
	python -m black api || echo "Black not installed"
