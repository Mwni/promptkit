class BaseLLM:
    def __call__(self, messages, **config):
        raise NotImplemented()