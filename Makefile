.PHONY: test install clean coverage lint

# Python interpreter to use
PYTHON = python3

# Test files
TEST_FILES = tests/test_chaosencrypt_cli.py tests/test_semantic_clustering.py

# Default target
all: install test

# Install dependencies
install:
	$(PYTHON) -m pip install -r requirements.txt

# Run all tests
test:
	PYTHONPATH=. $(PYTHON) -m pytest $(TEST_FILES) -v

# Run tests with coverage report
coverage:
	PYTHONPATH=. $(PYTHON) -m pytest $(TEST_FILES) --cov=src --cov-report=term-missing -v

# Run linting (if you add flake8 or pylint later)
lint:
	$(PYTHON) -m flake8 src tests

# Clean up Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +

# Run tests in watch mode (requires pytest-watch)
watch:
	PYTHONPATH=. $(PYTHON) -m pytest_watch $(TEST_FILES) -v

# Run a specific test file
test-cli:
	PYTHONPATH=. $(PYTHON) -m pytest tests/test_chaosencrypt_cli.py -v

test-semantic:
	PYTHONPATH=. $(PYTHON) -m pytest tests/test_semantic_clustering.py -v

# Help target
help:
	@echo "Available targets:"
	@echo "  all        - Install dependencies and run tests (default)"
	@echo "  install    - Install project dependencies"
	@echo "  test       - Run all tests"
	@echo "  coverage   - Run tests with coverage report"
	@echo "  lint       - Run linting checks"
	@echo "  clean      - Clean up Python cache files"
	@echo "  watch      - Run tests in watch mode"
	@echo "  test-cli   - Run only CLI tests"
	@echo "  test-semantic - Run only semantic clustering tests"
	@echo "  help       - Show this help message" 