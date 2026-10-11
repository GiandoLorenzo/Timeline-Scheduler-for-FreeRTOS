# Timeline configuration tools

Requires Python 3; all tools use the standard library.

From the repository root:

```bash
python3 Tools/scheduler_generator.py --help
python3 Tools/scheduler_generator.py -c Tools/system_config.json -o Tools/generated_main.c
python3 -m unittest discover -s Tools/tests -v
```

The JSON is an object with `system_name`, `timeline_period`, `tick_rate_hz` and `tasks`. The generator validates:

- Printable ASCII system name, 1-80 characters; safely escaped in C output.
- Positive integer period (maximum 32-bit unsigned value) and tick rate (maximum 1,000,000 Hz).
- Between 1 and 10 tasks, with unique names starting with a letter and containing only letters, digits and underscores, maximum 40 characters.
- Task type exactly `HARD` or `SOFT`.
- Integer windows satisfying `0 <= start_tick < end_tick <= timeline_period`.
- Stack size from 256 to 4096 words; default 256. Total allocation must still fit the application's FreeRTOS heap.
- No overlapping HARD windows. SOFT windows may overlap HARD windows.

It estimates utilization from allocated HARD windows, not measured or proven WCET. A successful analysis does not establish execution-time schedulability.

The generated source includes compile-time checks against `configTIMELINE_PERIOD` and `configTICK_RATE_HZ`. Update `Demo/FreeRTOSConfig.h` if changing those JSON fields. Copy the source to `Demo/generated_main.c` and build with `make -C Demo all MAIN_SOURCE=generated_main.c` after cleaning.

Task functions are stubs: simulated work followed by self-suspension. Task names in FreeRTOS debug data may be truncated by `configMAX_TASK_NAME_LEN`.

`run_qemu_test.py` checks explicit test markers and saves logs in `artifacts/`; use it after compiling a scenario as documented in the root README.
