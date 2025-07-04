# Data and Model Versioning

This project uses **DVC** (Data Version Control) to manage large training datasets.
All raw and intermediate datasets live outside the Git repository and are
referenced through lightweight `.dvc` files. Run `dvc pull` to fetch the
current versions or `dvc push` to upload updates to the configured remote
storage. Each commit captures the dataset state so experiments remain
reproducible.

Model artifacts are tracked with **MLflow**. Training runs log metrics and
artifacts to the `mlruns/` directory (or your configured MLflow server). Use the
MLflow UI to compare runs and promote models to production. The recommended
workflow is to push finalized models to the `models/` directory and reference
them by their MLflow run ID and semantic version.
