class BaseLLM:
    def __call__(self, messages):
        raise NotImplemented()