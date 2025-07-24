class AdminClient:
    def __init__(self, *a, **k):
        pass

    def list_topics(self, *a, **k):
        class Meta:
            brokers = {}
            topics = {}
        return Meta()

    def list_consumer_groups(self, *a, **k):
        return []

    def list_consumer_group_offsets(self, *a, **k):
        return {}
