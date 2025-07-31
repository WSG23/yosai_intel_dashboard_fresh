class TrulyUnifiedCallbacks:
    def trigger(self, *args, **kwargs):
        pass

    async def trigger_async(self, *args, **kwargs):
        return []


CallbackManager = TrulyUnifiedCallbacks
