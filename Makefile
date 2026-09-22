install:
	python -m pip install -e '.[test]'
run:
	uvicorn services.api.main:app --reload
demo:
	python scripts/run_demo.py
test:
	pytest -q
