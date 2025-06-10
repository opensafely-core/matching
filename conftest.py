import os
import sys


# Ensure that we can do `from analysis.match import ...` in tests
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "analysis"))
