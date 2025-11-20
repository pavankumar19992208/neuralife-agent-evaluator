import yaml
from pathlib import Path
from .schema import TestSuite

def load_suite(path):
    p = Path(path)
    raw = yaml.safe_load(p.read_text())
    suite = TestSuite(**raw)
    return suite

def load_all_tests(tests_dir="tests/examples"):
    from glob import glob
    for f in glob(f"{tests_dir}/*.yaml"):
        yield load_suite(f)