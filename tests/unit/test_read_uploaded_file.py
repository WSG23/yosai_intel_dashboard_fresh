from yosai_intel_dashboard.src.services.data_processing.file_processor import FileProcessor
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder


def test_read_uploaded_file_basic():
    df = DataFrameBuilder().add_column("a", [1, 2]).add_column("b", [3, 4]).build()
    contents = UploadFileBuilder().with_dataframe(df).as_base64()
    processor = FileProcessor()
    loaded, size = processor.read_uploaded_file(contents, "sample.csv")
    assert len(loaded) == len(df)
    assert size > 0
