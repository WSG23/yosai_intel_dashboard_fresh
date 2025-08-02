#!/usr/bin/env python3
import re
from pathlib import Path

# Define replacement patterns
replacements = [
    # config imports
    (
        r"from config import",
        "from yosai_intel_dashboard.src.infrastructure.config import",
    ),
    (r"from config\.", "from yosai_intel_dashboard.src.infrastructure.config."),
    # models imports
    (
        r"from models import",
        "from yosai_intel_dashboard.src.core.domain.entities import",
    ),
    (r"from models\.ml\.", "from yosai_intel_dashboard.src.models.ml."),
    (r"from models\.", "from yosai_intel_dashboard.src.core.domain.entities."),
    # services imports
    (r"from services import", "from yosai_intel_dashboard.src.services import"),
    (r"from services\.", "from yosai_intel_dashboard.src.services."),
]

# Files to update
doc_files = [
    "docs/architecture.md",
    "docs/feature_pipeline.md",
    "docs/integration-guide.md",
    "docs/secret_management.md",
    "docs/performance_monitoring.md",
    "docs/monitoring.md",
    "docs/models_guide.md",
    "docs/training_pipeline.md",
]

for file_path in doc_files:
    if not Path(file_path).exists():
        continue

    print(f"Updating {file_path}...")

    with open(file_path, "r") as f:
        content = f.read()

    original_content = content

    # Apply replacements
    for old_pattern, new_pattern in replacements:
        content = re.sub(old_pattern, new_pattern, content)

    # Add note at top if changed
    if content != original_content:
        if not content.startswith("> **Note**"):
            note = (
                "> **Note**: Import paths updated for clean architecture. "
                "Legacy imports are deprecated.\n\n"
            )
            content = note + content

    with open(file_path, "w") as f:
        f.write(content)

    print(f"  ✓ Updated {file_path}")

print("\n✅ Documentation update complete!")
