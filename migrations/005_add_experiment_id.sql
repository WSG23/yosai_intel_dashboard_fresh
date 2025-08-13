ALTER TABLE model_registry ADD COLUMN IF NOT EXISTS experiment_id VARCHAR(64) NOT NULL DEFAULT 'default';
CREATE INDEX IF NOT EXISTS idx_model_registry_name_experiment ON model_registry (name, experiment_id);
