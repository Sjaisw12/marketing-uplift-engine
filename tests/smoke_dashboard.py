"""Run with only app/requirements.txt: five pages plus a real local HTTP server.

No pytest, research dependencies, raw data, models, network service or deployment.
The server binds loopback only and is terminated before this script exits.
"""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "app/streamlit_app.py"


def main():
    test = AppTest.from_file(str(ENTRYPOINT), default_timeout=20).run()
    assert not test.exception
    pages = [
        "Overview",
        "Policy comparisons",
        "Sensitivity explorer",
        "Budget illustration",
        "Models & limitations",
    ]
    for page in pages[1:]:
        test.radio(key="page").set_value(page).run()
        assert not test.exception, page
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(ENTRYPOINT),
            "--server.headless=true",
            "--server.address=127.0.0.1",
            f"--server.port={port}",
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # Proxy-free only for this local health check; inherited external network
    # authentication/TLS/proxy settings are never modified.
    opener = build_opener(ProxyHandler({}))
    try:
        deadline, healthy = time.monotonic() + 20, False
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Local Streamlit server exited before becoming healthy")
            try:
                with opener.open(f"http://127.0.0.1:{port}/_stcore/health", timeout=1) as response:
                    healthy = response.status == 200 and response.read() == b"ok"
                if healthy:
                    break
            except OSError:
                time.sleep(0.1)
        assert healthy, "Local Streamlit health check did not pass"
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "python": sys.version.split()[0],
                    "pages_executed": pages,
                    "http_health": 200,
                    "server_scope": "loopback only; terminated on exit",
                },
                indent=2,
            )
        )
    finally:
        process.terminate()
        try:
            process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)


if __name__ == "__main__":
    main()
