class Consumer:
    def __init__(self, *a, **k):
        pass

    def get_watermark_offsets(self, *a, **k):
        return (0, 0)

    def close(self):
        pass

class Producer:
    def __init__(self, *a, **k):
        pass
