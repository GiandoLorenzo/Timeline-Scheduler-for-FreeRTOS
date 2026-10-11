#include "FreeRTOS.h"
#include "task.h"

#include "uart.h"


#define mainTASK_PRIORITY    ( tskIDLE_PRIORITY + 2 )
static volatile BaseType_t xFirstTaskRan = pdFALSE;

void vTaskFunction(void *pvParameters);
void vTaskFunction2(void *pvParameters);


int main(int argc, char **argv){

	(void) argc;
	(void) argv;

    UART_init();

	xTaskCreate(
		// Function which implements the task
		vTaskFunction,
		// Name of the task (debug purposes, not used by the kernel)
		"Task1",
		// Stack to allocate to the task
		configMINIMAL_STACK_SIZE,
		// Parameter passed to the task. Not needed for Hello World example
		NULL,
		// Priority assigned to the task
		mainTASK_PRIORITY,
		// Task handle. Not required
		NULL
	);

    xTaskCreate(
		// Function which implements the task
		vTaskFunction2,
		// Name of the task (debug purposes, not used by the kernel)
		"Task2",
		// Stack to allocate to the task
		configMINIMAL_STACK_SIZE,
		// Parameter passed to the task. Not needed for Hello World example
		NULL,
		// Priority assigned to the task
		mainTASK_PRIORITY+1,
		// Task handle. Not required
		NULL
	);

	// Give control to the scheduler
	vTaskStartScheduler();

	// If everything ok should never reach here
    for( ; ; );
}

/* Task Function */
void vTaskFunction(void *pvParameters) {

	// Avoid warning about unused pvParameters
	(void) pvParameters;

    for (;;) {

        // Task code: print a message
        UART_printf("Hello, World!\n");
        xFirstTaskRan = pdTRUE;

        // Delay for 1 second
        vTaskDelay(pdMS_TO_TICKS(5000));
    }
}

void vTaskFunction2(void *pvParameters) {

	// Avoid warning about unused pvParameters
	(void) pvParameters;

    for (;;) {

        // Task code: print a message
        if (xFirstTaskRan) { UART_printf("TEST_RESULT 0 PASS\n"); }

        // Delay for 1 second
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}