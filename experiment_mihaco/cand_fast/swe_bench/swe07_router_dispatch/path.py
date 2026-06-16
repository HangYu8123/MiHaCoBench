def split_path(p: str) -> list[str]:
    """Normalize a URL path into its NON-EMPTY segments."""
    return [seg for seg in p.strip('/').split('/') if seg]
