from .enrich_record import *
# ---------------------------------------------------------------------------
# 6. PROCESSOR REGISTRY — handlers keyed by media kind
# ---------------------------------------------------------------------------

class ProcessorRegistry:
    """
    Register and dispatch processing functions by media kind.
    Each processor is a callable(record, config) -> None.
    Multiple processors per kind are supported (run in registration order).
    """

    def __init__(self):
        self._handlers = OrderedDict()   # kind -> [callable, ...]

    def register(self, kind, handler):
        """Register a handler for a media kind."""
        if kind not in self._handlers:
            self._handlers[kind] = []
        self._handlers[kind].append(handler)
        return handler

    def process(self, record, config):
        """Run all registered handlers for the record's kind."""
        kind = record.get("kind", "")
        for handler in self._handlers.get(kind, []):
            handler(record, config)

    def process_all(self, records, config):
        """Process an iterable of records."""
        for record in records:
            self.process(record, config)
