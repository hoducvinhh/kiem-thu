import os
import re
import time
from pathlib import Path

import pytest


_TEST_START_TIMES = {}
_SCREENSHOT_DIR = Path(__file__).parent / "assets" / "screenshots"


def _duration_for(nodeid, fallback):
    start_time = _TEST_START_TIMES.get(nodeid)
    if not start_time:
        return f"{fallback:.2f}s"
    return f"{time.perf_counter() - start_time:.2f}s"


def _short_failure(report):
    if not report.longrepr:
        return ""
    failure_text = str(report.longrepr).strip().splitlines()
    for line in reversed(failure_text):
        line = line.strip()
        if line and not line.startswith("_"):
            return f" - {line[:220]}"
    return ""


def _safe_filename(nodeid):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", nodeid).strip("_")


def _active_driver(item):
    for fixture_name in ("driver", "authenticated_driver"):
        browser = item.funcargs.get(fixture_name)
        if browser:
            return browser
    return None


def _save_screenshot(item, report):
    browser = _active_driver(item)
    if not browser:
        return None

    _SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    screenshot_path = _SCREENSHOT_DIR / f"{_safe_filename(report.nodeid)}_{report.outcome}.png"
    browser.save_screenshot(str(screenshot_path))
    return screenshot_path


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return

    should_capture = report.failed or os.getenv("SCREENSHOT_EACH_TEST", "0") == "1"
    if not should_capture:
        return

    try:
        screenshot_path = _save_screenshot(item, report)
    except Exception as error:
        print(f"[SCREENSHOT] Could not capture {report.nodeid}: {error}", flush=True)
        return

    if screenshot_path:
        print(f"[SCREENSHOT] {screenshot_path}", flush=True)


def pytest_runtest_logstart(nodeid, location):
    print(f"\n[RUNNING] {nodeid}", flush=True)


def pytest_runtest_setup(item):
    _TEST_START_TIMES[item.nodeid] = time.perf_counter()


def pytest_runtest_logreport(report):
    if report.when == "setup" and report.failed:
        duration = _duration_for(report.nodeid, report.duration)
        print(f"[ERROR  ] {report.nodeid} ({duration}){_short_failure(report)}", flush=True)
        return

    if report.when == "setup" and report.skipped:
        duration = _duration_for(report.nodeid, report.duration)
        print(f"[SKIP   ] {report.nodeid} ({duration}){_short_failure(report)}", flush=True)
        return

    if report.when != "call":
        return

    duration = _duration_for(report.nodeid, report.duration)

    if report.passed:
        status = "PASS"
    elif report.failed:
        status = "FAIL"
    elif report.skipped:
        status = "SKIP"
    else:
        status = report.outcome.upper()

    print(f"[{status:<7}] {report.nodeid} ({duration}){_short_failure(report)}", flush=True)
