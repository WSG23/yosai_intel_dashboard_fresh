#!/bin/bash
# Concatenate unused helper scripts in the repository root

files=(
    add_navbar_callbacks.py
    add_navbar_callbacks_minimal.py
    add_navbar_to_minimal.py
    add_original_navbar.py
    add_register_callback_method.py
    add_routing.py
    app_factory_simple_fix.py
    check_fix.py
    check_fixes.py
    column_mapper.py
    enable_router_fix.py
    example_ai_adapter.py
    force_initial_callback.py
    minimal_dash_pages_test.py
    minimal_test.py
    minimal_test_app.py
    nuclear_fix_dependencies.py
    persistence_diagnostics.py
    project_dash_diagnosis.py
    restore_original_navbar.py
    run_focused_audit.py
    ui_callback_controller.py
    ui_tracker.py
    upload_callback_standalone.py
    upload_handler.py
    validate_core_import.py
    validate_future_imports.py
    validate_imports.py
    working_app_test.py
)

for f in "${files[@]}"; do
    echo "========== $f =========="
    if [[ -f "$f" ]]; then
        cat "$f"
    else
        echo "File not found: $f" >&2
    fi
    echo
done
