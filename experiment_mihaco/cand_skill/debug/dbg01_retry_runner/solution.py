def run_with_retries(attempts: list[bool], max_retries: int) -> dict:
    max_attempts = max_retries + 1
    count = 0
    status = "running"
    for outcome in attempts[:max_attempts]:
        count += 1
        if outcome:
            status = "succeeded"
            break
        if count >= max_attempts:
            status = "failed"
    # Post-loop guard: if the attempts list was exhausted before the budget
    # was consumed (len(attempts) < max_attempts), status is still "running".
    if status == "running":
        status = "failed"
    return {"status": status, "attempts": count}
