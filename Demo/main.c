#include "FreeRTOS.h"
#include "task.h"
#include <stdio.h>
#include "uart.h"
#include <semphr.h>

#include <timeline.h>


/* * Busy Wait Helper to simulate CPU load
 */

static SemaphoreHandle_t xSem;

static void BusyWait( int sequence )
{
    volatile int i;
    for( i = 0; i < sequence * 10000; i++ )
    {
        /* Burn Cycles */
    }
}

/* * Timeline Task A - HARD Real-Time (Window: 0-200)
 */
static void vTaskA( void *pvParameters )
{
    ( void ) pvParameters;
    
    UART_printf( "Task A [0-200] Job START\r\n" );
        
    /* Simulate 20 units of work */
    BusyWait( 20 );
        
    UART_printf( "Task A [0-200] Job DONE\r\n" );
        
    vTaskSuspend( NULL );
}

/* * Timeline Task B - SOFT Real-Time (Window: 100-300)
 */
static void vTaskB( void *pvParameters )
{
    ( void ) pvParameters;
    
    UART_printf( "Task B [100-300] Job START\r\n" );
        
    BusyWait( 20 );
        
    UART_printf( "Task B [100-300] Job DONE\r\n" );
        
    vTaskSuspend( NULL );
}

/* * Timeline Task D - HARD Real-Time (Window: 250-350)
 */
static void vTaskD( void *pvParameters )
{
    ( void ) pvParameters;
    
    UART_printf( "Task D [250-350] Job START\r\n" );
        
    BusyWait( 20 );
        
    UART_printf( "Task D [250-350] Job DONE\r\n" );
        
    vTaskSuspend( NULL );
}

/* * Timeline Task C - HARD Real-Time (Window: 500-600)
 */
static void vTaskC( void *pvParameters )
{
    ( void ) pvParameters;
    
    UART_printf( "Task C [500-600] Job START\r\n" );
        
    BusyWait( 20 );
        
    UART_printf( "Task C [500-600] Job DONE\r\n" );
        
    vTaskSuspend( NULL );
}

static void vTaskE( void *pvParameters )
{
    ( void ) pvParameters;
    
    UART_printf( "I IPOTETICALLY NOT RUN\r\n" );
        
    BusyWait( 20 );
        
    UART_printf( "OK THERE IS AN ERROR\r\n" );
        
    vTaskSuspend( NULL );
}


/* * ----------------------------------------------------------
 * System Schedule Configuration
 * ----------------------------------------------------------
 */
const TimelineTaskConfig_t xSystemSchedule[] = 
{
    /* Name      Function   Param   Stack   Start   End     Type */
    { "TaskA",   vTaskA,    NULL,   512,    0,      200,    TASK_TYPE_HARD, NULL },
    { "TaskB",   vTaskB,    NULL,   512,    100,    300,    TASK_TYPE_SOFT, NULL },
    { "TaskD",   vTaskD,    NULL,   512,    250,    350,    TASK_TYPE_HARD, NULL },
    { "TaskE",   vTaskE,    NULL,   512,    700,    600,    TASK_TYPE_HARD, NULL }, //TASK WILL NOT ADDED!!
    
    {NULL}
};

int main( int argc, char **argv )
{
    ( void ) argc;
    ( void ) argv;

    UART_init();
    
    UART_printf( "Timeline Scheduler Demo Starting...\r\n" );


    /* * Configure the Scheduler 
     * This function parses the table above, creates the tasks, 
     * and sets their initial state (Ready or Suspended).
     */
    vConfigureScheduler( xSystemSchedule );

    /* Start the scheduler */
    vTaskStartScheduler();

    /* Should never reach here */
    for( ;; );
}