def run_with_retries(attempts: list[bool], max_retries: int) -> dict:
    max_attempts = max_retries + 1
    count = 0
    status = "failed"
    for outcome in attempts[:max_attempts]:
        count += 1
        if outcome:
            status = "succeeded"
            break
    return {"status": status, "attempts": count}
