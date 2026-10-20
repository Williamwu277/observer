from models import IncompleteScrapeError


def validate_greenhouse_jobs(payload: dict) -> list[dict]:
    """Reject truncated or malformed feeds before their jobs reach reconciliation."""
    jobs = payload.get("jobs")
    total = payload.get("meta", {}).get("total")
    if not isinstance(jobs, list) or type(total) is not int or len(jobs) != total:
        raise IncompleteScrapeError("Greenhouse job count does not match meta.total")

    ids = [job.get("id") for job in jobs]
    if any(type(job_id) is not int or job_id <= 0 for job_id in ids):
        raise IncompleteScrapeError("Greenhouse feed has an invalid job ID")
    if len(set(ids)) != len(ids):
        raise IncompleteScrapeError("Greenhouse feed has duplicate job IDs")
    return jobs
