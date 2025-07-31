import importlib, sys
module = importlib.import_module('yosai_intel_dashboard.src.services')
sys.modules[__name__] = module
