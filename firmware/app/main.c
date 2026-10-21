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
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include <NoRTOS.h>
#include <ti/drivers/GPIO.h>
#include <ti/drivers/UART2.h>
#include <ti/drivers/Power.h>
#include <ti/drivers/power/PowerCC23X0.h>
#include <ti/devices/DeviceFamily.h>
#include DeviceFamily_constructPath(driverlib/pmctl.h)
#include DeviceFamily_constructPath(inc/hw_types.h)
#include DeviceFamily_constructPath(inc/hw_memmap.h)
#include DeviceFamily_constructPath(inc/hw_evtull.h)

#include "ti_drivers_config.h"

static UART2_Handle uartLog;
static volatile bool irqSeen;
static volatile uint32_t irqCount;

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
    irqCount++;
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

    /* BTN-1 floats on this LaunchPad (the board file's external pull-up is
     * not there in practice: the pin stayed low after the first press).
     * TODO: move the pull-up into boards/launchpad.syscfg via SysConfig. */
    GPIO_setConfig(CONFIG_GPIO_BTN_IRQ, GPIO_CFG_IN_PU | GPIO_CFG_IN_INT_FALLING);
    GPIO_setCallback(CONFIG_GPIO_BTN_IRQ, irqCallback);
    GPIO_enableInt(CONFIG_GPIO_BTN_IRQ);

    uint32_t ticks = 0;
    while (1)
    {
        GPIO_toggle(CONFIG_GPIO_LED_HEARTBEAT);
        /* Once a second, so the UART wiring can be checked without a reset */
        if ((++ticks & 1) == 0)
        {
            /* Reset reason repeated here: the banner is gone before a
             * terminal can reconnect after a power cycle */
            char line[80];
            snprintf(line, sizeof line, "tick %lu btn=%u irqs=%lu rst=%s\r\n", (unsigned long)(ticks / 2),
                     (unsigned)GPIO_read(CONFIG_GPIO_BTN_IRQ), (unsigned long)irqCount,
                     resetReasonName(resetReason));
            logStr(line);
        }
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
    /* Power_init (inside Board_init) leaves only the RTC as a standby wakeup
     * source, so a GPIO edge during standby is lost. IRQ_N must wake us. */
    HWREG(EVTULL_BASE + EVTULL_O_WKUPMASK) |= EVTULL_WKUPMASK_AON_IOC_COMB_M;
    NoRTOS_start();
#ifdef BRINGUP_NO_STANDBY
    Power_setConstraint(PowerLPF3_DISALLOW_STANDBY);
#endif
    mainThread(resetReason);
    return 0;
}
