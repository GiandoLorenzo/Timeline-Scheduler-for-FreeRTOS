#!/usr/bin/env python3
import json
import argparse
import sys
import os
import re

# Configuration Constants
DEFAULT_CONFIG_FILE = "system_config.json"
OUTPUT_FILE = "../Demo/generated_main.c"

def validate_schedule(config):
    """
    Validates the task schedule.
    Rules:
    1. HARD tasks must not overlap with other HARD tasks.
    2. All tasks must be within [0, timeline_period].
    3. start_tick < end_tick.
    4. CPU Utilization check.
    """
    if not isinstance(config, dict):
        print("ERROR: Configuration must be a JSON object.")
        return False
    tasks = config.get("tasks", [])
    period = config.get("timeline_period", 1000)
    tick_rate = config.get("tick_rate_hz", 1000)
    system_name = config.get("system_name", "FreeRTOS System")
    if (type(period) is not int or not 1 <= period <= 0xFFFFFFFF or
            type(tick_rate) is not int or not 1 <= tick_rate <= 1000000):
        print("ERROR: Period and tick rate must be positive bounded integers.")
        return False
    if not isinstance(system_name, str) or not 1 <= len(system_name) <= 80 or any(ord(c) < 32 or ord(c) > 126 for c in system_name):
        print("ERROR: system_name must contain 1-80 printable ASCII characters.")
        return False
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 10:
        print("ERROR: Define between 1 and 10 tasks.")
        return False
    names = set()
    for task in tasks:
        if not isinstance(task, dict):
            print("ERROR: Each task must be an object.")
            return False
        name = task.get("name")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,39}", name) or name in names:
            print("ERROR: Task names must be unique C identifiers of 1-40 characters, starting with a letter.")
            return False
        names.add(name)
        if task.get("type") not in ("HARD", "SOFT"):
            print("ERROR: Task type must be HARD or SOFT.")
            return False
        if any(type(task.get(key)) is not int for key in ("start_tick", "end_tick")):
            print("ERROR: Task windows must use integer ticks.")
            return False
        stack = task.get("stack_size", 256)
        if type(stack) is not int or not 256 <= stack <= 4096:
            print("ERROR: Stack size must be an integer between 256 and 4096 words.")
            return False
    
    print("--------------------------------------------------")
    print(f"Analyzing Schedulability for {len(tasks)} tasks...")
    print(f"Timeline Period: {period} ticks")
    print("--------------------------------------------------")
    
    # Check boundaries
    for task in tasks:
        if task["start_tick"] < 0 or task["end_tick"] > period:
            print(f"ERROR: Task '{task['name']}' [{task['start_tick']}-{task['end_tick']}] is out of bounds [0-{period}].")
            print("Status: NOT FEASIBLE")
            return False
        if task["start_tick"] >= task["end_tick"]:
            print(f"ERROR: Task '{task['name']}' has invalid duration (start={task['start_tick']}, end={task['end_tick']}).")
            print("Status: NOT FEASIBLE")
            return False


    # Check overlaps for HARD tasks
    hard_tasks = sorted([t for t in tasks if t["type"] == "HARD"], key=lambda x: x["start_tick"])
    
    for i in range(len(hard_tasks) - 1):
        current_task = hard_tasks[i]
        next_task = hard_tasks[i+1]
        
        # Check overlap: Start of next < End of current
        if next_task["start_tick"] < current_task["end_tick"]:
            print(f"ERROR: HARD Task Overlap detected: '{current_task['name']}' ends at {current_task['end_tick']}, but '{next_task['name']}' starts at {next_task['start_tick']}.")
            print("Status: NOT FEASIBLE")
            return False

    # Check CPU Utilization
    total_hard_duration = sum(t["end_tick"] - t["start_tick"] for t in hard_tasks)
    utilization = (total_hard_duration / period) * 100.0
    
    print(f"Total HARD Task Duration: {total_hard_duration} ticks")
    print(f"CPU Utilization (HARD): {utilization:.2f}%")
    
    if utilization > 100.0:
        print(f"ERROR: CPU Utilization exceeds 100% ({utilization:.2f}%).")
        print("Status: NOT FEASIBLE")
        return False
    elif utilization > 90.0:
        print(f"WARNING: High CPU Utilization ({utilization:.2f}%). System may be unstable.")
    
    # Check SRT Starvation
    soft_tasks = [t for t in tasks if t["type"] == "SOFT"]
    if soft_tasks and utilization >= 100.0:
        print("WARNING: SOFT tasks are defined but HARD tasks consume 100% of the timeline. SOFT tasks will starve.")

    print("Status: FEASIBLE")
    print("--------------------------------------------------")
    return True

def generate_c_code(config, output_path):
    """
    Generates the C source code for the FreeRTOS application.
    """
    tasks = config.get("tasks", [])
    system_name = config.get("system_name", "FreeRTOS System")
    
    # Sort tasks by start time for readability in the array
    sorted_tasks = sorted(tasks, key=lambda x: x["start_tick"])

    c_code = f"""/*
 * Timeline Scheduler - Generated Main File
 * This file is automatically generated by scheduler_generator.py.
 * Do not edit manually.
 */

#include "FreeRTOS.h"
#include "task.h"
#include "timeline.h"
#include "uart.h"
#include "semphr.h"
#include <stdio.h>

_Static_assert(configTIMELINE_PERIOD == {config.get('timeline_period', 1000)}, "Set configTIMELINE_PERIOD to match the JSON configuration");
_Static_assert(configTICK_RATE_HZ == {config.get('tick_rate_hz', 1000)}, "Set configTICK_RATE_HZ to match the JSON configuration");

/*-----------------------------------------------------------
 * Task Forward Declarations
 *----------------------------------------------------------*/
"""
    
    for task in sorted_tasks:
        c_code += f"static void v{task['name']}( void *pvParameters );\n"

    c_code += """
/*-----------------------------------------------------------
 * Main Entry Point
 *----------------------------------------------------------*/
int main( void )
{
    /* Initialize UART for output */
    UART_init();
    UART_printf( "\\r\\n--------------------------------------------------\\r\\n" );
    UART_printf( """ + json.dumps("System: " + system_name + "\r\n") + """ );
    UART_printf( "Status: System Initializing...\\r\\n" );
    UART_printf( "--------------------------------------------------\\r\\n" );

    /*
     * Define the Schedule Table.
     * Order: Name, Function, Parameters, StackDepth, StartTick, EndTick, Type, SemHandler
     */
    static const TimelineTaskConfig_t xScheduleTable[] = {
"""

    for task in sorted_tasks:
        task_type_enum = "TASK_TYPE_" + task['type'].upper()
        # Ensure stack_size is present
        stack_size = task.get("stack_size", 256)
        
        c_code += f"""        {{ "{task['name']}", v{task['name']}, NULL, {stack_size}, {task['start_tick']}, {task['end_tick']}, {task_type_enum}, NULL }},\n"""

    c_code += """        { NULL, NULL, NULL, 0, 0, 0, 0, NULL } /* Sentinel / End Marker */
    };

    /* Configure the Scheduler with the generated table */
    UART_printf( "Configuring Scheduler...\\r\\n" );
    vConfigureScheduler( xScheduleTable );

    /* Start the Scheduler */
    UART_printf( "Starting Scheduler...\\r\\n" );
    vTaskStartScheduler();

    /* We should never reach here if the scheduler starts successfully */
    for( ;; );
}

/*-----------------------------------------------------------
 * Task Implementations
 *----------------------------------------------------------*/
"""

    for task in sorted_tasks:
        c_code += f"""
static void v{task['name']}( void *pvParameters )
{{
    ( void ) pvParameters; /* Unused parameter */
    
    /* Defines for task timing (for reference/debugging) */
    const TickType_t xStart = {task['start_tick']};
    const TickType_t xEnd = {task['end_tick']};
    (void)xStart; (void)xEnd;

    char buf[128];
    
    /* Initial Print */
    /* Initial Print - Removed to match requested format */
    /* snprintf( buf, sizeof( buf ), "Task {task['name']} started.\\r\\n" ); */
    /* UART_printf( buf ); */


    for( ;; )
    {{
        /* Print Job Start */
        snprintf( buf, sizeof( buf ), "{task['name']} [{task['start_tick']}-{task['end_tick']}] Job START\\r\\n" );
        UART_printf( buf );
        
        /* Simulated Workload */
        volatile uint32_t i;
        for( i = 0; i < 5000; i++ ) {{ __asm( "nop" ); }}
        
        /* Print Job Done */
        snprintf( buf, sizeof( buf ), "{task['name']} [{task['start_tick']}-{task['end_tick']}] Job DONE\\r\\n" );
        UART_printf( buf );
        
        /* Suspend Self - The Scheduler will resume this task in the next period */
        vTaskSuspend( NULL );
    }}
}}
"""

    try:
        with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(c_code)
        print(f"SUCCESS: Generated {output_path}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to write output file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate FreeRTOS timeline schedule from JSON config.")
    parser.add_argument("-c", "--config", default=DEFAULT_CONFIG_FILE, help="Path to JSON configuration file.")
    parser.add_argument("-o", "--output", default=OUTPUT_FILE, help="Path to output C file.")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        print(f"ERROR: Configuration file '{args.config}' not found.")
        sys.exit(1)
        
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeError) as e:
        print(f"ERROR: Failed to parse JSON: {e}")
        sys.exit(1)
        
    if validate_schedule(config):
        if not generate_c_code(config, args.output):
            sys.exit(1)
    else:
        print("ABORTED: Schedule generation failed due to validation errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()
