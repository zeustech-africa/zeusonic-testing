# Simple developer convenience Makefile

.PHONY: health-local health-docker

health-local:
	python3 scripts/health_check.py --url http://127.0.0.1:8000/api/v1/health

health-docker:
	python3 scripts/health_check.py --url http://localhost:8000/api/v1/health
