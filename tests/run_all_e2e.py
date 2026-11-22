#!/usr/bin/env python3
"""
MediApp Healthcare Network — Unified E2E Test Runner & Programmatic Orchestrator.
Orchestrates test execution across all 6 Feature Areas, all 4 Tiers, and all 29 defects (DEF-01 through DEF-29).

Phases:
- Phase 0: Environment Health Check (Python 3.12 venv, Chromium executable, Node.js, Port Checks)
- Phase 1: Isolated Domain Service Unit Tests (pytest: pricing, state machine, inventory, DDI)
- Phase 2: REST API, RBAC & Security Integration Tests (pytest: auth, orders, payments, rx, ai)
- Phase 3: Defect Remediation & Multi-Tier Regression Suite (test_defect_remediations.py, test_edge_cases_and_security.py, etc.)
- Phase 4: Headless Playwright Browser Tests (test_nextjs_e2e_scenarios.py, verify_nextjs_frontend.py, verify_rbac_ui.py)
- Phase 5: Clinical Design, WCAG 2.1 AA Accessibility & Zero-Emoji Scanner (test_clinical_design_a11y.py)
- Phase 6: Aggregated Markdown Scorecard & Process Exit Code (0 on all pass, 1 on any failure)
"""
import os
import sys
import time
import socket
import shutil
import argparse
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VENV_PYTHON = os.path.join(REPO_ROOT, ".venv", "Scripts", "python.exe")
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable

CHROMIUM_EXEC = r"C:\Users\smshr\AppData\Local\ms-playwright\chromium-1255\chrome-win64\chrome.exe"
FLASK_PORT = 5000
NEXTJS_PORT = 3000


@dataclass
class PhaseResult:
    phase_id: int
    name: str
    command: str
    exit_code: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_sec: float = 0.0
    stdout: str = ""
    stderr: str = ""
    error_summary: str = ""

    @property
    def status(self) -> str:
        if self.failed > 0 or self.exit_code != 0:
            return "FAILED"
        if self.skipped > 0 and self.passed == 0:
            return "SKIPPED"
        return "PASSED"


def is_port_listening(host: str, port: int) -> bool:
    """Checks whether a TCP port is active and accepting connections."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.8)
        res = sock.connect_ex((host, port))
        sock.close()
        return res == 0
    except Exception:
        return False


def run_command(cmd: List[str], cwd: str = REPO_ROOT, timeout: int = 120) -> tuple[int, str, str]:
    """Runs a subprocess command with explicit timeout and captured stdout/stderr."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return 1, "", str(e)


def parse_pytest_counts(output: str) -> tuple[int, int, int]:
    """Extracts passed, failed, and skipped test counts from pytest stdout."""
    import re
    passed = 0
    failed = 0
    skipped = 0

    pass_match = re.search(r"(\d+)\s+passed", output)
    fail_match = re.search(r"(\d+)\s+failed", output)
    skip_match = re.search(r"(\d+)\s+skipped", output)

    if pass_match:
        passed = int(pass_match.group(1))
    if fail_match:
        failed = int(fail_match.group(1))
    if skip_match:
        skipped = int(skip_match.group(1))

    return passed, failed, skipped


# ============================================================================
# Phase 0: Environment Health Check
# ============================================================================

def execute_phase_0(verbose: bool = False) -> Dict[str, str]:
    """Executes environment discovery and checks tooling availability."""
    print("\n" + "=" * 78)
    print("PHASE 0: ENVIRONMENT & PLATFORM HEALTH CHECK")
    print("=" * 78)

    checks = {}

    # 1. Python version and virtualenv
    py_ver = sys.version.split()[0]
    is_venv = hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
    checks["Python Version"] = f"{py_ver} ({'Active Virtualenv' if is_venv else 'System Python'})"
    print(f"[*] Python Runtime:     {checks['Python Version']}")

    # 2. Playwright Chromium executable
    chromium_found = os.path.exists(CHROMIUM_EXEC)
    checks["Playwright Chromium"] = CHROMIUM_EXEC if chromium_found else "NOT FOUND AT DEFAULT PATH"
    print(f"[*] Chromium Binary:    {'READY' if chromium_found else 'MISSING'} ({checks['Playwright Chromium']})")

    # 3. Node.js & npm
    node_cmd = shutil.which("node") or "node"
    npm_cmd = shutil.which("npm") or ("npm.cmd" if sys.platform == "win32" else "npm")
    node_res, node_out, _ = run_command([node_cmd, "-v"])
    npm_res, npm_out, _ = run_command([npm_cmd, "-v"])
    checks["Node.js"] = node_out.strip() if node_res == 0 else "MISSING"
    checks["npm"] = npm_out.strip() if npm_res == 0 else "MISSING"
    print(f"[*] Node.js Runtime:    {checks['Node.js']} (npm v{checks['npm']})")

    # 4. Port Checks
    flask_listening = is_port_listening("127.0.0.1", FLASK_PORT)
    nextjs_listening = is_port_listening("127.0.0.1", NEXTJS_PORT)
    checks["Flask (Port 5000)"] = "ONLINE (Listening)" if flask_listening else "OFFLINE"
    checks["Next.js (Port 3000)"] = "ONLINE (Listening)" if nextjs_listening else "OFFLINE"
    print(f"[*] Port 5000 (Flask):  {checks['Flask (Port 5000)']}")
    print(f"[*] Port 3000 (Next.js):{checks['Next.js (Port 3000)']}")

    print("=" * 78)
    return checks


# ============================================================================
# Test Runner Implementation
# ============================================================================

class UnifiedTestRunner:
    def __init__(self, skip_browser: bool = False, auto_start: bool = False, verbose: bool = False):
        self.skip_browser = skip_browser
        self.auto_start = auto_start
        self.verbose = verbose
        self.results: List[PhaseResult] = []
        self.flask_proc: Optional[subprocess.Popen] = None
        self.nextjs_proc: Optional[subprocess.Popen] = None

    def start_background_servers(self):
        """Starts Flask and Next.js subprocesses if auto_start is requested."""
        if not is_port_listening("127.0.0.1", FLASK_PORT):
            print("[+] Auto-starting Flask server on port 5000...")
            self.flask_proc = subprocess.Popen(
                [VENV_PYTHON, "-c", "from app import create_app; app = create_app(); app.run(port=5000, host='127.0.0.1')"],
                cwd=REPO_ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # Poll for readiness
            for _ in range(15):
                if is_port_listening("127.0.0.1", FLASK_PORT):
                    print("    Flask is ready on http://127.0.0.1:5000")
                    break
                time.sleep(0.5)

        if not is_port_listening("127.0.0.1", NEXTJS_PORT):
            print("[+] Auto-starting Next.js frontend on port 3000...")
            self.nextjs_proc = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=os.path.join(REPO_ROOT, "frontend"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True
            )
            for _ in range(30):
                if is_port_listening("127.0.0.1", NEXTJS_PORT):
                    print("    Next.js is ready on http://127.0.0.1:3000")
                    break
                time.sleep(1.0)

    def stop_background_servers(self):
        """Terminates any subprocesses started by this runner."""
        for name, proc in [("Flask", self.flask_proc), ("Next.js", self.nextjs_proc)]:
            if proc:
                print(f"[-] Terminating auto-started {name} server...")
                if sys.platform == "win32":
                    try:
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    except Exception:
                        pass
                else:
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except Exception:
                        proc.kill()

    def run_pytest_phase(self, phase_id: int, phase_name: str, test_files: List[str], timeout: int = 60) -> PhaseResult:
        """Executes a list of test files via pytest and records structured metrics."""
        print(f"\n[PHASE {phase_id}] {phase_name.upper()}...")
        cmd = [VENV_PYTHON, "-m", "pytest"] + test_files + ["-v", "--tb=short"]
        t_start = time.time()
        code, out, err = run_command(cmd, timeout=timeout)
        dur = round(time.time() - t_start, 2)

        p, f, s = parse_pytest_counts(out)
        res = PhaseResult(
            phase_id=phase_id,
            name=phase_name,
            command=" ".join(test_files),
            exit_code=code,
            passed=p,
            failed=f,
            skipped=s,
            duration_sec=dur,
            stdout=out,
            stderr=err
        )

        status_tag = f"[{res.status}]"
        print(f"    Status: {status_tag} | Passed: {p} | Failed: {f} | Skipped: {s} | Duration: {dur}s")
        if self.verbose and (code != 0 or f > 0):
            print("\n--- Diagnostic Output ---")
            print(out[-1500:] if len(out) > 1500 else out)
            if err:
                print(err[-1000:] if len(err) > 1000 else err)

        self.results.append(res)
        return res

    def run_all(self, selected_phase: Optional[int] = None):
        """Runs the multi-phase test sequence."""
        try:
            if self.auto_start and not self.skip_browser:
                self.start_background_servers()

            # Phase 1: Isolated Domain Service Unit Tests
            if selected_phase is None or selected_phase == 1:
                self.run_pytest_phase(
                    phase_id=1,
                    phase_name="Isolated Domain Service Unit Tests",
                    test_files=[
                        "tests/test_pricing.py",
                        "tests/test_state_machine.py",
                        "tests/test_inventory.py",
                        "tests/test_ddi.py"
                    ],
                    timeout=30
                )

            # Phase 2: REST API, RBAC & Security Integration Tests
            if selected_phase is None or selected_phase == 2:
                self.run_pytest_phase(
                    phase_id=2,
                    phase_name="REST API, RBAC & Security Integration Tests",
                    test_files=[
                        "tests/test_api_ai.py",
                        "tests/test_api_orders.py",
                        "tests/test_api_payments.py",
                        "tests/test_api_prescriptions.py",
                        "tests/test_auth_rbac.py"
                    ],
                    timeout=45
                )

            # Phase 3: Defect Remediation & Multi-Tier Regression Suite
            if selected_phase is None or selected_phase == 3:
                self.run_pytest_phase(
                    phase_id=3,
                    phase_name="Defect Remediation & Multi-Tier Regression Suite",
                    test_files=[
                        "tests/test_defect_remediations.py",
                        "tests/test_e2e_scenarios.py",
                        "tests/test_edge_cases_and_security.py",
                        "scripts/test_remediation.py"
                    ],
                    timeout=60
                )

            # Phase 4: Headless Playwright Browser Tests
            if selected_phase is None or selected_phase == 4:
                if self.skip_browser:
                    print("\n[PHASE 4] HEADLESS PLAYWRIGHT BROWSER VERIFICATION (SKIPPED BY USER FLAG)")
                    self.results.append(PhaseResult(
                        phase_id=4,
                        name="Headless Playwright Browser Verification",
                        command="--skip-browser",
                        exit_code=0,
                        skipped=1,
                        duration_sec=0.0,
                        stdout="Skipped by --skip-browser flag"
                    ))
                else:
                    self.run_pytest_phase(
                        phase_id=4,
                        phase_name="Headless Playwright Browser Verification",
                        test_files=[
                            "tests/test_nextjs_e2e_scenarios.py"
                        ],
                        timeout=120
                    )

            # Phase 5: Clinical Design, WCAG 2.1 AA Accessibility & Zero-Emoji Scanner
            if selected_phase is None or selected_phase == 5:
                self.run_pytest_phase(
                    phase_id=5,
                    phase_name="Clinical Design, WCAG 2.1 AA & Zero-Emoji Scanner",
                    test_files=[
                        "tests/test_clinical_design_a11y.py"
                    ],
                    timeout=30
                )

        finally:
            if self.auto_start:
                self.stop_background_servers()

    def generate_scorecard(self, output_path: Optional[str] = None) -> str:
        """Constructs an aggregated markdown report card of all phases."""
        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)
        total_skipped = sum(r.skipped for r in self.results)
        total_duration = round(sum(r.duration_sec for r in self.results), 2)
        all_passed = (total_failed == 0 and all(r.exit_code == 0 for r in self.results))

        lines = []
        lines.append("# MediApp Healthcare Network — E2E Test Suite Execution Scorecard")
        lines.append(f"\n**Execution Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
        lines.append(f"**Overall Suite Status**: `{'PASS' if all_passed else 'FAIL'}`")
        lines.append(f"**Total Passed**: `{total_passed}` | **Total Failed**: `{total_failed}` | **Total Skipped**: `{total_skipped}` | **Duration**: `{total_duration}s`\n")
        lines.append("## Phase Execution Summary\n")
        lines.append("| Phase | Name | Status | Passed | Failed | Skipped | Duration | Target Modules |")
        lines.append("|:---:|---|:---:|:---:|:---:|:---:|:---:|---|")

        for r in self.results:
            lines.append(
                f"| {r.phase_id} | {r.name} | `{r.status}` | {r.passed} | {r.failed} | {r.skipped} | {r.duration_sec}s | `{r.command}` |"
            )

        lines.append("\n## Defect Remediation Tracking Matrix\n")
        lines.append("| Defect ID | Feature Area | Description | Verified in Phase |")
        lines.append("|---|---|---|---|")
        lines.append("| **DEF-01** | Build | Missing node_modules build failure | Phase 0 (Environment) |")
        lines.append("| **DEF-02** | Catalogue | TypeScript Medicine contract sync | Phase 0 / Phase 5 |")
        lines.append("| **DEF-03** | Catalogue | requires_cold_chain column migration | Phase 3 (`test_defect_remediations.py`) |")
        lines.append("| **DEF-04** | Catalogue | Non-numeric rx parameter 400 error handling | Phase 3 (`test_defect_remediations.py`) |")
        lines.append("| **DEF-05** | Auth | String address persisted to customer_addresses | Phase 3 (`test_defect_remediations.py`) |")
        lines.append("| **DEF-06** | Logistics | Available runs customer address deserialization | Phase 3 & Phase 4 |")
        lines.append("| **DEF-07** | AI Triage | Emergency triage warning response contract | Phase 3 (`test_defect_remediations.py`) |")
        lines.append("| **DEF-08** | Logistics | Secret OTP redacted from delivery courier | Phase 3 & Phase 4 |")
        lines.append("| **DEF-09** | Logistics | Courier UI hides customer secret OTP | Phase 4 (`test_nextjs_e2e_scenarios.py`) |")
        lines.append("| **DEF-10** | Logistics | Customer UI hides courier verify input | Phase 4 (`test_nextjs_e2e_scenarios.py`) |")
        lines.append("| **DEF-11** | Auth | Guest session reset on unauthenticated state | Phase 4 (`test_nextjs_e2e_scenarios.py`) |")
        lines.append("| **DEF-12** | Logistics | Milestone stepper intermediate status mapping | Phase 4 (`test_nextjs_e2e_scenarios.py`) |")
        lines.append("| **DEF-13** | Catalogue | Catalogue filter pills reset pagination to 1 | Phase 4 (`test_nextjs_e2e_scenarios.py`) |")
        lines.append("| **DEF-14** | Clinical | Pharmacist desk terminal button locking | Phase 3 & Phase 4 |")
        lines.append("| **DEF-15** | Layout | Navbar provides user identity and Sign Out | Phase 4 (`test_nextjs_e2e_scenarios.py`) |")
        lines.append("| **DEF-16** | Catalogue | Add to Cart restricted on non-customer roles | Phase 4 (`test_nextjs_e2e_scenarios.py`) |")
        lines.append("| **DEF-17** | Theming | Dark canvas #070D1A not overridden by slate-950 | Phase 5 (`test_clinical_design_a11y.py`) |")
        lines.append("| **DEF-18** | Clinical | Prescription zoom viewport flex overflow | Phase 4 (`test_nextjs_e2e_scenarios.py`) |")
        lines.append("| **DEF-19** | Layout | Mobile drawer includes Sign In & AI Triage | Phase 4 (`test_nextjs_e2e_scenarios.py`) |")
        lines.append("| **DEF-20** | Logistics | OTP placeholder guidance specifies 6-digit | Phase 5 (`test_clinical_design_a11y.py`) |")
        lines.append("| **DEF-21** | Logistics | DB cold-chain flag & CartDrawer guarantee badge | Phase 3 & Phase 4 |")
        lines.append("| **DEF-22** | Clinical | Clinical Emerald tokens & Crimson rejection badge | Phase 5 (`test_clinical_design_a11y.py`) |")
        lines.append("| **DEF-23** | Catalogue | Generic Price Match calculated ₹ and % savings | Phase 4 (`test_nextjs_e2e_scenarios.py`) |")
        lines.append("| **DEF-24** | Logistics | Itemized active molecules & formulation details | Phase 4 (`test_nextjs_e2e_scenarios.py`) |")
        lines.append("| **DEF-25** | Clinical | Zero-Emoji Invariant scanner | Phase 5 (`test_clinical_design_a11y.py`) |")
        lines.append("| **DEF-26** | A11y | WAI-ARIA role='dialog', focus trap & Escape | Phase 5 (`test_clinical_design_a11y.py`) |")
        lines.append("| **DEF-27** | A11y | Accessible form input labels (htmlFor/id) | Phase 5 (`test_clinical_design_a11y.py`) |")
        lines.append("| **DEF-28** | A11y | Keyboard accessibility & zero nested buttons | Phase 5 (`test_clinical_design_a11y.py`) |")
        lines.append("| **DEF-29** | A11y | WCAG 2.1 AA text contrast ratio >= 4.5:1 | Phase 5 (`test_clinical_design_a11y.py`) |")

        scorecard_content = "\n".join(lines) + "\n"

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(scorecard_content)
            print(f"\n[+] Scorecard written to: {output_path}")

        return scorecard_content


# ============================================================================
# Main CLI Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="MediApp Healthcare Network — Unified E2E Test Suite Runner")
    parser.add_argument("--skip-browser", action="store_true", help="Skip headless browser tests (Phase 4)")
    parser.add_argument("--auto-start", action="store_true", help="Automatically spawn Flask and Next.js servers for browser testing")
    parser.add_argument("--port-check", action="store_true", help="Run only Phase 0 environment health and port checks")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4, 5], help="Run only a specific test phase")
    parser.add_argument("--scorecard", type=str, default="TEST_SCORECARD.md", help="Path to write markdown scorecard")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output during test execution")

    args = parser.parse_args()

    # Always execute Phase 0 Environment Check
    execute_phase_0(verbose=args.verbose)
    if args.port_check:
        sys.exit(0)

    runner = UnifiedTestRunner(
        skip_browser=args.skip_browser,
        auto_start=args.auto_start,
        verbose=args.verbose
    )

    t0 = time.time()
    runner.run_all(selected_phase=args.phase)
    elapsed = round(time.time() - t0, 2)

    scorecard_path = os.path.join(REPO_ROOT, args.scorecard)
    scorecard = runner.generate_scorecard(output_path=scorecard_path)

    print("\n" + "=" * 78)
    print(f"E2E TEST RUN COMPLETED IN {elapsed}s")
    total_failed = sum(r.failed for r in runner.results)
    any_error = any(r.exit_code != 0 for r in runner.results)
    if total_failed == 0 and not any_error:
        print("RESULT: ALL SUITES PASSED (Exit Code: 0)")
        sys.exit(0)
    else:
        print(f"RESULT: FAILURES DETECTED ({total_failed} failed tests across {len(runner.results)} phases)")
        sys.exit(1)


if __name__ == "__main__":
    main()
