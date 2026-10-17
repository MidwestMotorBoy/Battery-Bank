/*
 * MonolithDev MCU firmware, bring-up skeleton (NoRTOS).
 *
 * Day 1 on the LP-EM-CC2340R53: proves the build, the probe and the UART.
 * - prints a banner and the reset reason on the XDS110 UART (115200 8N1)
 * - blinks the heartbeat LED at 1 Hz
 * - logs each falling edge on the IRQ input (BTN-1 on the LaunchPad)
 */

#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>

#include <NoRTOS.h>
#include <ti/drivers/GPIO.h>
#include <ti/drivers/UART2.h>
#include <ti/devices/DeviceFamily.h>
#include DeviceFamily_constructPath(driverlib/pmctl.h)

#include "ti_drivers_config.h"

static UART2_Handle uartLog;
static volatile bool irqSeen;

static void logStr(const char *s)
{
    UART2_write(uartLog, s, strlen(s), NULL);
}

static const char *resetReasonName(uint32_t reason)
{
    switch (reason)
    {
        case PMCTL_RESET_POR:          return "POR";
        case PMCTL_RESET_PIN:          return "PIN";
        case PMCTL_RESET_VDDS:         return "VDDS loss";
        case PMCTL_RESET_VDDR:         return "VDDR loss";
        case PMCTL_RESET_WATCHDOG:     return "WATCHDOG";
        case PMCTL_RESET_SYSTEM:       return "SYSTEM (software)";
        case PMCTL_RESET_CPU:          return "CPU";
        case PMCTL_RESET_LOCKUP:       return "LOCKUP";
        case PMCTL_RESET_SWD:          return "SWD (debugger)";
        case PMCTL_RESET_TSD:          return "THERMAL SHUTDOWN";
        case PMCTL_RESET_SHUTDOWN_IO:  return "wake from shutdown (IO)";
        case PMCTL_RESET_SHUTDOWN_SWD: return "wake from shutdown (SWD)";
        case PMCTL_RESET_LFXT:         return "LF clock loss";
        default:                       return "other";
    }
}

static void irqCallback(uint_least8_t index)
{
    (void)index;
    irqSeen = true;
}

static void mainThread(uint32_t resetReason)
{
    UART2_Params params;
    UART2_Params_init(&params);
    params.baudRate = 115200;
    uartLog = UART2_open(CONFIG_UART_LOG, &params);

    logStr("\r\n\r\nMonolithDev firmware, bring-up skeleton\r\n");
    logStr("Built " __DATE__ " " __TIME__ "\r\n");
    logStr("Reset reason: ");
    logStr(resetReasonName(resetReason));
    logStr("\r\n");

    GPIO_setCallback(CONFIG_GPIO_BTN_IRQ, irqCallback);
    GPIO_enableInt(CONFIG_GPIO_BTN_IRQ);

    while (1)
    {
        GPIO_toggle(CONFIG_GPIO_LED_HEARTBEAT);
        if (irqSeen)
        {
            irqSeen = false;
            logStr("IRQ: falling edge\r\n");
        }
        usleep(500000);
    }
}

int main(void)
{
    /* Read before anything else can disturb the reset status */
    uint32_t resetReason = PMCTLGetResetReason();

    Board_init();
    NoRTOS_start();
    mainThread(resetReason);
    return 0;
}
