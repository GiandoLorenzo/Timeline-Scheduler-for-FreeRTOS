/* Timeline regression scenarios.
 * Copyright (C) 2024 - Released under FreeRTOS MIT License
 * SPDX-License-Identifier: MIT
 */
#include "FreeRTOS.h"
#include "task.h"
#include "timeline.h"
#include "uart.h"
#include <stdint.h>
#include <stdio.h>
#ifndef TEST_NUMBER
#define TEST_NUMBER 3
#endif
#if TEST_NUMBER < 1 || TEST_NUMBER > 8
#error TEST_NUMBER must be between 1 and 8
#endif
static volatile TickType_t starts[5];
static volatile BaseType_t done[5];
static volatile BaseType_t started[5];
static volatile unsigned count, polling;
static volatile BaseType_t resourceHeld, resourceError;
static SemaphoreHandle_t semaphore;
static TickType_t relativeTick(void) { return xTaskGetTickCount() % 1000U; }
/* CPU work remains runnable, so deadline/preemption tests do not test blocking. */
static void work(TickType_t duration) {
    TickType_t start = xTaskGetTickCount();
    while ((TickType_t)(xTaskGetTickCount() - start) < duration) { __asm volatile("nop"); }
}
static void job(void *parameter) {
    unsigned id = (unsigned)(uintptr_t)parameter;
    starts[id] = relativeTick();
    started[id] = pdTRUE;
    done[id] = pdFALSE;
    if (TEST_NUMBER == 1 && id == 0) { work(110); }
    else if (TEST_NUMBER == 3 && id == 0) { work(140); }
    else if (TEST_NUMBER == 6) { work(40); }
    else if (TEST_NUMBER == 5) { work(90); }
    else { work(10); }
    done[id] = pdTRUE;
    vTaskSuspend(NULL);
}
static void takeResource(void *parameter) {
    (void)parameter;
    if (xSemaphoreTake(semaphore, 0) == pdTRUE) { count++; }
    else { resourceError = pdTRUE; }
    vTaskSuspend(NULL);
}
static void checkResource(void *parameter) {
    (void)parameter;
    if (xSemaphoreTake(semaphore, 0) == pdFALSE) { resourceHeld = pdTRUE; }
    else { resourceError = pdTRUE; xSemaphoreGive(semaphore); }
    vTaskSuspend(NULL);
}
static void pollJob(void *parameter) {
    unsigned id = (unsigned)(uintptr_t)parameter;
    if (polling != id) { resourceError = pdTRUE; }
    polling++;
    vTaskSuspend(NULL);
}
static void report(void *parameter) {
    (void)parameter;
    BaseType_t pass = pdFALSE;
    char buffer[80];
    switch (TEST_NUMBER) {
        case 1: pass = !done[0] && done[1] && starts[0] == 0 && starts[1] == 101; break;
        case 2: pass = done[0] && done[1] && starts[0] == 0 && starts[1] == 100; break;
        case 3: pass = done[0] && done[1] && starts[0] == 0 && starts[1] == 100; break;
        case 4: pass = done[0] && starts[0] == 50; break;
        case 5:
            pass = pdTRUE;
            for (unsigned id = 0; id < 5; id++) {
                if (!done[id] || starts[id] != id * 100U) { pass = pdFALSE; }
            }
            break;
        case 6: pass = started[0] && starts[0] == 0 && !done[0]; break;
        case 7:
            /* Wait for the second major frame before evaluating reset. */
            if (xTaskGetTickCount() < 1000U) { vTaskSuspend(NULL); return; }
            pass = count >= 2 && resourceHeld && !resourceError;
            break;
        case 8: pass = polling == 2 && !resourceError; polling = 0; break;
    }
    snprintf(buffer, sizeof(buffer), "TEST_RESULT %d %s\r\n", TEST_NUMBER, pass ? "PASS" : "FAIL");
    UART_printf(buffer);
    vTaskSuspend(NULL);
}
#define ENTRY(name, function, id, start, end, kind, sem) \
    {name, function, (void *)(uintptr_t)(id), 512, start, end, kind, sem}
int main(void) {
    UART_init();
    _Static_assert(configTIMELINE_PERIOD == 1000U, "Tests require a 1000-tick major frame");
#if TEST_NUMBER == 1
    const TimelineTaskConfig_t schedule[] = {
        ENTRY("A", job, 0, 0, 100, TASK_TYPE_HARD, NULL),
        ENTRY("B", job, 1, 50, 150, TASK_TYPE_HARD, NULL),
#elif TEST_NUMBER == 2
    const TimelineTaskConfig_t schedule[] = {
        ENTRY("A", job, 0, 0, 100, TASK_TYPE_HARD, NULL),
        ENTRY("B", job, 1, 100, 200, TASK_TYPE_HARD, NULL),
#elif TEST_NUMBER == 3
    const TimelineTaskConfig_t schedule[] = {
        ENTRY("Soft", job, 0, 0, 200, TASK_TYPE_SOFT, NULL),
        ENTRY("Hard", job, 1, 100, 150, TASK_TYPE_HARD, NULL),
#elif TEST_NUMBER == 4
    const TimelineTaskConfig_t schedule[] = {
        ENTRY("Timed", job, 0, 50, 150, TASK_TYPE_HARD, NULL),
#elif TEST_NUMBER == 5
    const TimelineTaskConfig_t schedule[] = {
        ENTRY("S0", job, 0, 0, 100, TASK_TYPE_HARD, NULL),
        ENTRY("S1", job, 1, 100, 200, TASK_TYPE_HARD, NULL),
        ENTRY("S2", job, 2, 200, 300, TASK_TYPE_HARD, NULL),
        ENTRY("S3", job, 3, 300, 400, TASK_TYPE_HARD, NULL),
        ENTRY("S4", job, 4, 400, 500, TASK_TYPE_HARD, NULL),
#elif TEST_NUMBER == 6
    const TimelineTaskConfig_t schedule[] = {
        ENTRY("Overrun", job, 0, 0, 20, TASK_TYPE_HARD, NULL),
#elif TEST_NUMBER == 7
    semaphore = xSemaphoreCreateBinary();
    configASSERT(semaphore != NULL);
    configASSERT(xSemaphoreGive(semaphore) == pdTRUE);
    const TimelineTaskConfig_t schedule[] = {
        ENTRY("Take", takeResource, 0, 0, 400, TASK_TYPE_SOFT, &semaphore),
        ENTRY("Check", checkResource, 0, 500, 900, TASK_TYPE_HARD, NULL),
#elif TEST_NUMBER == 8
    const TimelineTaskConfig_t schedule[] = {
        ENTRY("PollA", pollJob, 0, 0, 400, TASK_TYPE_SOFT, NULL),
        ENTRY("PollB", pollJob, 1, 500, 900, TASK_TYPE_HARD, NULL),
#endif
        ENTRY("Reporter", report, 0, 950, 990, TASK_TYPE_HARD, NULL),
        {0}
    };
    vConfigureScheduler(schedule);
    vTaskStartScheduler();
    UART_printf("ERROR: Scheduler failed to start\r\n");
    for (;;) {}
}
