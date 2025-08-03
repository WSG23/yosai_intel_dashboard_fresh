Developer Guides
================

Test Migration Script
---------------------

The ``tools/migrate_tests.py`` helper updates test files to the current
import layout and adds ``pytest.importorskip`` checks for optional
dependencies.

Running
^^^^^^^

Preview changes without touching the files:

.. code-block:: bash

   python tools/migrate_tests.py --dry-run

Remove ``--dry-run`` to apply the edits.

Interpreting the Report
^^^^^^^^^^^^^^^^^^^^^^^

Each ``Would update`` line in dry-run mode indicates a file that will be
modified.  After applying the changes the script prints ``Updated`` for
files it rewrote.  Any entries that could not be migrated automatically
are grouped at the end of the output under ``needs manual review``.

Reviewing Manual Items
^^^^^^^^^^^^^^^^^^^^^^

For every path listed under ``needs manual review``:

#. Open the file and inspect the indicated line.
#. Replace custom ``sys.modules`` manipulations with
   ``safe_import`` or ``import_optional`` from ``tests.import_helpers``.
#. Re-run the script to ensure the item no longer appears.
