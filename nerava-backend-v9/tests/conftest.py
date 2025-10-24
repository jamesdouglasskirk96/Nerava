import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
def pytest_addoption(parser):
    parser.addoption("--slow", action="store_true", help="include slow tests")
