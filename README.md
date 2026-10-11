# FreeRTOS Timeline Scheduler

An experimental timeline scheduler developed for an embedded operating systems course by Group 36. It extends a modified FreeRTOS kernel and provides Cortex-M3 demonstrations on QEMU's `mps2-an385` board.

The scheduler chooses HARD tasks during their configured windows and lets SOFT tasks use available time. With `configUSE_TIMELINE=0`, the priority scheduler remains available.

## Quick start

Use Linux or WSL with GNU Make, Python 3, `arm-none-eabi-gcc`, Newlib and `qemu-system-arm`. Windows PowerShell can run the Python tools; the Makefiles require a Linux shell.

On Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y make python3 gcc-arm-none-eabi libnewlib-arm-none-eabi qemu-system-arm gdb-multiarch
make -C Demo all
make -C Demo qemu_start
```

QEMU runs indefinitely. Press **Ctrl+A, then X** to exit the interactive demo.

With Docker Desktop or Docker Engine, run from the repository root:

```bash
docker build -f DOCKERFILE/Dockerfile -t freertos-timeline .
docker run --rm -it freertos-timeline bash
```

Inside the container, use the same `make` and `python3` commands. The image copies the project at build time; rebuild it after changing sources. It runs as a non-root user and contains no GitLab runner or registration credentials. Containers share the host kernel and do not guarantee isolation against malicious code.

## Repository layout

| Directory | Purpose |
| --- | --- |
| `FreeRTOS-Kernel/` | Vendored FreeRTOS source with timeline modifications |
| `Demo/` | Example timeline application |
| `DemoPriority/` | Priority scheduler demonstration, timeline disabled |
| `DemoTest/` | Eight timeline regression scenarios |
| `Tools/` | JSON configuration, code generator, tests and QEMU result checker |
| `DOCKERFILE/` | Linux build environment |

The PDF report is historical coursework documentation. The source and this README describe the current behavior; the report may describe earlier tests or runner setup.

## Scheduler behavior and limits

- `configUSE_TIMELINE=1` selects the timeline scheduler. The supported demonstration target is single-core Cortex-M3 with the GCC ARM_CM3 port.
- `configTIMELINE_PERIOD` defines the major frame in ticks; its default is 1000. The demos use `configTICK_RATE_HZ=1000`, so one tick represents one millisecond.
- At most 10 timeline tasks can be registered. Call `vConfigureScheduler()` once, before starting the scheduler, with a table ending in a zero sentinel.
- Windows currently include both endpoints: `[start_tick, end_tick]`. When HARD windows overlap, the first ready HARD entry in the registration table wins. Adjacent jobs should finish before their shared boundary. The Python generator rejects overlapping HARD windows.
- A task outside its window is excluded from selection. A deadline overrun does not delete its TCB or perform application cleanup; the task restarts at the next major-frame reset.
- At each major frame, registered tasks have their execution context reinitialized. Global variables, peripherals and external effects are **not** automatically reset.
- Tasks should complete their work and suspend themselves. Prefer non-blocking polling. Do not dynamically delete registered timeline tasks; the registry does not support their removal.
- `configUSE_TL_FORCERESETSEMAPHORE` can return registered binary/counting semaphores at major-frame boundaries. Do not register mutexes for ISR-based forced release. Resource recovery does not undo a partially completed application operation.
- Stack overflow and allocation-failure hooks are disabled in the original demo configurations. Enable and implement the corresponding hooks before extending the demos to larger applications.

This is a teaching prototype. Window checks do not prove WCET, interrupt latency, real-hardware timing guarantees or suitability for safety-critical systems.

## Run the tests

```bash
python3 -m unittest discover -s Tools/tests -v
make -C DemoPriority clean
make -C DemoPriority all
python3 Tools/run_qemu_test.py --project DemoPriority --test 0

make -C DemoTest clean
make -C DemoTest all EXTRA_CFLAGS="-DTEST_NUMBER=6"
python3 Tools/run_qemu_test.py --project DemoTest --test 6
```

Repeat the last three commands with test numbers 1 through 8. Clean between scenarios because Make does not track changes to command-line compiler flags.

| Test | Check |
| --- | --- |
| 0 | Both priority demo tasks execute |
| 1 | An overrunning HARD task loses selection after its inclusive window; overlapping task B starts at tick 101 |
| 2 | Adjacent HARD jobs start at ticks 0 and 100 |
| 3 | A CPU-bound SOFT job is interrupted by a HARD job starting at tick 100 |
| 4 | A task starts at tick 50 |
| 5 | Five sequential jobs start at their configured boundaries and complete |
| 6 | A CPU-bound 40-tick job cannot complete within its 0-20 window |
| 7 | A held binary semaphore is restored across a major-frame boundary |
| 8 | Two tasks exchange and verify a shared polling counter |

The checker requires `TEST_RESULT N PASS`, rejects explicit failures and kernel errors, and saves logs under `artifacts/`. It stops QEMU after a deliberate timeout; an early emulator exit fails the check. Passing these scenarios is regression evidence, not a complete proof of scheduler correctness.

## Generate an application

Edit `Tools/system_config.json`, then run from the repository root:

```bash
python3 Tools/scheduler_generator.py -c Tools/system_config.json -o Tools/generated_main.c
cp Tools/generated_main.c Demo/generated_main.c
make -C Demo clean
make -C Demo all MAIN_SOURCE=generated_main.c
make -C Demo qemu_start
```

The output contains task stubs with simulated work. Replace their bodies with application logic. Set `configTIMELINE_PERIOD` and `configTICK_RATE_HZ` in `Demo/FreeRTOSConfig.h` to match the JSON; generated compile-time checks reject mismatches. See [Tools documentation](Tools/README.md) for validation rules. The generator checks window consistency and allocation of HARD windows, not execution-time feasibility.

## Continuous integration

GitHub Actions runs Python checks and a matrix of QEMU scenarios from `.github/workflows/ci.yml`. The existing `.gitlab-ci.yml` is retained for a separately configured GitLab environment and uses the same result checker. GitLab runner credentials belong outside the repository; use trusted, appropriately isolated runners.

## Debugging

`make -C Demo qemu_debug` pauses the emulator and exposes GDB only at `127.0.0.1:1234`. Connect with `gdb-multiarch Demo/Output/demo.elf` and `target remote 127.0.0.1:1234`. Do not expose this unauthenticated debug interface to other machines.

## Attribution and licenses

Original coursework: Group 36. Student identifiers and personal PDF metadata have been removed from the public copy.

The project-level license is [GPL-3.0](LICENSE). Vendored FreeRTOS and files carrying MIT notices retain their [MIT license](FreeRTOS-Kernel/LICENSE.md) and original copyright notices. The project-level license does not replace third-party notices.

Upstream project: [FreeRTOS-Kernel](https://github.com/FreeRTOS/FreeRTOS-Kernel). This snapshot identifies itself as `V11.1.0+` in `include/task.h`; its manifest has an older development-version label. The exact upstream commit is unavailable in this downloaded copy, so no unverified commit is claimed. Timeline changes are mainly in `tasks.c`, `include/task.h` and `include/timeline.h`. Only the Cortex-M3 demonstrations are targeted by this project's regression suite; other bundled ports have not been validated with the modifications.

See [SECURITY.md](SECURITY.md) for security scope and [PUBLISHING.md](PUBLISHING.md) for GitHub publication steps.
