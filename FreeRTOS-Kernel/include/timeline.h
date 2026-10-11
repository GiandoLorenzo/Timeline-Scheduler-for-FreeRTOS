#ifndef FREERTOS_TIMELINE_H_
#define FREERTOS_TIMELINE_H_

#include "FreeRTOS.h"
#include "task.h"
#include "semphr.h"

#ifndef configTIMELINE_PERIOD
    #define configTIMELINE_PERIOD 1000U
#endif

    typedef struct {
        const char * pcName;                 /* Task Name */
        TaskFunction_t pxTaskCode;           /* Function to execute */
        void * pvParameters;                 /* Parameters */
        configSTACK_DEPTH_TYPE uxStackDepth; /* Stack Size */
        TickType_t xTimeStart;               /* Start Tick */
        TickType_t xTimeEnd;                 /* End Tick */
        TaskTimeType_t xTaskType;            /* HARD or SOFT */
        SemaphoreHandle_t *xSemHandler;

        

    } TimelineTaskConfig_t;

    void vConfigureScheduler( const TimelineTaskConfig_t *pxScheduleTable );

#endif
