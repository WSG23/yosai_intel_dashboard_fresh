import sys

# Provide backward compatibility for old import paths
from . import models as _models
from . import src as _src

sys.modules.setdefault(__name__ + ".models", _models)
sys.modules.setdefault(__name__ + ".src", _src)
