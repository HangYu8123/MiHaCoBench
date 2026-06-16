from router import Router


class App:
    def __init__(self) -> None:
        self._router = Router()

    def route(self, pattern: str, handler_name: str) -> None:
        """Register a route (delegates to Router.add)."""
        self._router.add(pattern, handler_name)

    def handle(self, path: str) -> dict:
        """Dispatch path. Returns:
             {"handler": <name>, "params": {...}}  on a match
             {"handler": None, "params": {}}       on no match
        """
        result = self._router.match(path)
        if result is not None:
            handler_name, params = result
            return {"handler": handler_name, "params": params}
        return {"handler": None, "params": {}}
