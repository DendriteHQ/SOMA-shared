"""Coarse classes for the errors a sandbox run can end with.

Used to group failures per sandbox (``sandbox_dispatches.error_class``) so a host that
keeps failing for its own reasons stands out from failures every host sees, such as
an LLM provider outage. The class is for reporting only; retry policy lives in the
auto-run-restarter.

Rules are checked in order, most specific first. Keep class names stable: they are
stored, and dashboards group by them.
"""
from __future__ import annotations

from typing import Callable, Optional

# Failures caused by the sandbox host itself rather than by the miner, the task or the
# LLM provider; a sandbox with many of these needs attention.
HOST_ERROR_CLASSES = frozenset(
    {
        "docker_sock_missing",
        "docker_daemon_unavailable",
        "docker_cgroup_start_failure",
        "docker_network_address_pool_exhausted",
        "dind_not_ready",
        "dind_sandbox_start_failure",
        "sandbox_disk_full",
        "missing_container_env_file",
        "container_startup_output_as_error",
        "runner_not_started",
        "runner_start_error",
        "runner_oom_killed",
    }
)


def _has(*needles: str) -> Callable[[str, str], bool]:
    """All needles occur in the error (case-sensitive)."""
    return lambda error, _lower: all(needle in error for needle in needles)


def _has_any(*needles: str) -> Callable[[str, str], bool]:
    """Any needle occurs in the lower-cased error."""
    return lambda _error, lower: any(needle in lower for needle in needles)


_RULES: tuple[tuple[str, Callable[[str, str], bool]], ...] = (
    # Runner lifecycle, as reported by the sandbox supervisor.
    ("runner_deadline_exceeded", _has("RunnerDeadlineExceeded")),
    ("runner_not_started", _has("RunnerNotStarted")),
    ("runner_start_error", _has("RunnerStartError")),
    ("runner_oom_killed", _has("RunnerExited", "oom_killed")),
    ("runner_exited", _has("RunnerExited")),
    # Sandbox host: Docker, dind, disk.
    ("docker_sock_missing", _has_any("docker.sock")),
    ("docker_daemon_unavailable", _has("Cannot connect to the Docker daemon")),
    ("sandbox_disk_full", _has("No space left on device")),
    ("dind_not_ready", _has("Isolated Docker daemon (dind) did not become ready")),
    (
        "dind_sandbox_start_failure",
        _has("Failed to start Copilot SWE sandbox inside the isolated Docker daemon"),
    ),
    ("docker_cgroup_start_failure", _has("unable to apply cgroup configuration")),
    (
        "docker_network_address_pool_exhausted",
        _has("all predefined address pools have been fully subnetted"),
    ),
    (
        "container_startup_output_as_error",
        lambda error, _lower: error.lstrip().startswith("Volume soma-copilot-"),
    ),
    (
        "missing_container_env_file",
        lambda error, _lower: error.lstrip().startswith("env file ") and " not found:" in error,
    ),
    # Benchmark repository preparation.
    ("git_clone_failure", _has("Failed to clone benchmark repository")),
    ("git_fetch_failure", _has("Failed to fetch benchmark base commit")),
    ("git_checkout_failure", _has("Failed to checkout benchmark base commit")),
    # LLM proxy reachability from inside the run.
    ("proxy_dns_failure", _has_any("enotfound", "name or service not known")),
    ("proxy_connection_refused", _has("Connection refused", "http://proxy:8080/")),
    (
        "proxy_connection_closed_early",
        _has("connection closed before message completed", "http://proxy:8080/"),
    ),
    # LLM provider answers.
    ("provider_model_404", _has("not found on provider", "HTTP 404")),
    ("provider_rate_limited", _has_any("429 rate limit", "rate limit exceeded")),
    ("provider_400", _has("400 Provider returned error")),
    ("provider_500", _has("500 Internal Server Error")),
    ("provider_502", _has_any("502 bad gateway", "http 502", "provider_unavailable")),
    ("provider_520", _has_any('"code":520', "error code: 520")),
    # Platform side, appended by the run coordinator.
    ("platform_patch_save_failed", _has("patch save failed")),
    ("unreported_failure", _has("Sandbox reported run as failed (ok_status=")),
    # Generic.
    ("timeout", _has_any("timeout", "timed out", "deadline")),
)


def classify_sandbox_error(error: Optional[str]) -> Optional[str]:
    """Class of a run's error message; None when there is no error to classify."""
    if error is None:
        return None
    text = error.strip()
    if not text:
        return None
    lower = text.lower()
    for name, matches in _RULES:
        if matches(text, lower):
            return name
    return "other"
