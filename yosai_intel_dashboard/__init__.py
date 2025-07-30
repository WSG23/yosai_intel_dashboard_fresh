import sys

# Provide backward compatibility for old import paths
import models as _models
import src as _src

sys.modules.setdefault(__name__ + ".models", _models)
sys.modules.setdefault(__name__ + ".src", _src)
