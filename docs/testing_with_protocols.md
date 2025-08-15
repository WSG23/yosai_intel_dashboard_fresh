# Testing with Protocols

This guide builds on [docs/test_architecture.md](test_architecture.md) and
explains the helper classes used to assemble test containers and fake services.
These utilities keep tests lightweight while exercising the same dependency
injection patterns as the production code.

## TestContainerBuilder

`TestContainerBuilder` lives in `tests/unit/builders.py`. It constructs a
`ServiceContainer` pre-populated with lightweight module stubs so importing heavy
packages like Dash or SQL parsing libraries is not required. Environment
variables commonly needed by the services can be initialised with
`with_env_defaults()` and all application services can be registered through
`with_all_services()`.

```python
from tests.unit.builders import TestContainerBuilder

container = (
    TestContainerBuilder()
    .with_env_defaults()
    .with_all_services()
    .build()
)
```

The resulting container behaves like the real application container but avoids
loading optional dependencies.

`TestContainerBuilder` also exposes helpers for registering fake services. These
return the builder instance so calls can be chained fluently:

```python
container = (
    TestContainerBuilder()
    .with_configuration()
    .with_unicode_processor()
    .with_file_processor()
    .build()
)
```

## Available Test Doubles

Several fake implementations reside in `tests/unit/fakes.py`:

- `FakeUploadStore` – in-memory `UploadStorageProtocol`
- `FakeUploadDataService` – minimal `UploadDataServiceProtocol`
- `FakeDeviceLearningService` – stub `DeviceLearningServiceProtocol`
- `FakeColumnVerifier` – simple `ColumnVerifierProtocol`
- `FakeConfigurationService` – lightweight `ConfigurationServiceProtocol`
- `FakeUnicodeProcessor` – cleans text for Unicode related tests

Use these fakes to isolate units under test and avoid filesystem or database
access.

## TestDataBuilder

`TestDataBuilder` helps create example analytics data frames. Call `add_row()` to
append entries and `build_dataframe()` to retrieve a `pandas.DataFrame`.
`as_upload_dict()` returns a mapping suitable for upload-based tests.

```python
from tests.unit.builders import TestDataBuilder

df = TestDataBuilder().add_row(person_id="u2").build_dataframe()
```

## Example Upload Processing Test

Many tests have been refactored to rely on these builders. The snippet below
shows a simplified upload-processing test that uses the container builder and
data builder together with the `async_runner` fixture:

```python
from tests.unit.builders import TestContainerBuilder, TestDataBuilder
from tests.utils.builders import UploadFileBuilder


def test_simple_upload_processing(async_runner):
    container = (
        TestContainerBuilder()
        .with_env_defaults()
        .with_all_services()
        .build()
    )
    processor = container.get("upload_processor")
    store = container.get("upload_storage")

    df = TestDataBuilder().add_row().build_dataframe()
    contents = UploadFileBuilder().with_dataframe(df).as_base64()

    _, _, info, *_ = async_runner(
        processor.process_uploaded_files([contents], ["sample.csv"])
    )

    assert info["sample.csv"]["rows"] == 1
    assert "sample.csv" in store.get_filenames()
```

This approach keeps test setup concise while still exercising the full upload
pipeline.
