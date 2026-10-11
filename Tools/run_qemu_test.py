"""Run a built QEMU demo and check explicit results; standard library only."""
import argparse
from pathlib import Path
import subprocess
import sys

def check_log(log, number):
    lines = {line.strip() for line in log.splitlines()}
    return (f"TEST_RESULT {number} PASS" in lines
            and not any(line.startswith("TEST_RESULT ") and line.endswith(" FAIL") for line in lines)
            and "ERROR:" not in log)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--test", type=int, choices=range(9), required=True)
    parser.add_argument("--timeout", type=float, default=8)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    log_path = Path("artifacts") / f"test{args.test}.log"
    log_path.parent.mkdir(exist_ok=True)
    command = ["qemu-system-arm", "-machine", "mps2-an385", "-cpu", "cortex-m3",
               "-kernel", str(Path(args.project) / "Output" / "demo.elf"),
               "-monitor", "none", "-nographic", "-serial", "stdio"]
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        timed_out = False
        try:
            output, _ = process.communicate(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            output, _ = process.communicate()
        log = output.decode("utf-8", errors="replace")
        log_path.write_text(log, encoding="utf-8")
        print(log)
        return 0 if timed_out and check_log(log, args.test) else 1
    except OSError as error:
        print(f"ERROR: Cannot start QEMU: {error}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
