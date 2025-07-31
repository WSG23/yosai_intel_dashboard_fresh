# Importing `TrulyUnifiedCallbacksType`

Use this template when you need the `TrulyUnifiedCallbacksType` for type hints without creating runtime dependencies:

```python
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from yosai_intel_dashboard.src.infrastructure.callbacks import TrulyUnifiedCallbacks as TrulyUnifiedCallbacksType
else:  # pragma: no cover - fallback runtime alias
    TrulyUnifiedCallbacksType = Any
```
