run:
	uvicorn nerava-backend-v9.app.main_simple:app --reload --port 8001

clean:
	./scripts/clean.sh

test:
	cd nerava-backend-v9 && python -m pytest tests/test_social_pool.py tests/test_feed.py -v

demo:
	./scripts/investor_demo.sh
