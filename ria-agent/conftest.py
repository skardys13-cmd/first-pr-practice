import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Tests must not inherit an operator, a home directory, or a pinned model from
# whatever shell they were started in. Anything RIA_AGENT_* is the install's
# configuration, and a test that reads it is testing the developer's machine.
for _name in [n for n in os.environ if n.startswith("RIA_AGENT_")]:
    del os.environ[_name]
