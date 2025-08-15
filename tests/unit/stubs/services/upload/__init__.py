from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)


class AISuggestionService:
    pass


class ChunkedUploadManager:
    pass


class ClientSideValidator:
    pass


class ModalService:
    pass


class UploadProcessingService:
    async_processor = None

    def __init__(self, store, *args, **kwargs):
        pass

    async def process_files(self, *a, **k):
        return ([], [], {}, [], {}, None, None)


def get_trigger_id():
    return "trig"
