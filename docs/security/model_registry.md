# Model Registry Security

The model registry stores serialized models on disk. Serialized Python objects
can execute arbitrary code when unpickled, so the registry applies two layers of
defense:

1. **Checksum verification** – The registry computes a SHA256 hash for each
   stored model. When loading, the hash of the stored file must match the
   checksum recorded in the metadata. Any modification of the file results in a
   checksum mismatch and the load is aborted.
2. **Restricted unpickling** – After verifying integrity, models are loaded with
   a custom `pickle.Unpickler` that only allows explicitly whitelisted classes
   (`AnomalyDetector` and `RiskScorer`). Attempts to deserialize other objects
   raise `pickle.UnpicklingError`.

These measures prevent tampering and block malicious payloads that might try to
execute code during deserialization.
