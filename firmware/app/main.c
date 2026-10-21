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
#include DeviceFamily_constructPath(driverlib/ckmd.h)

#include "ti_drivers_config.h"

/* Plan test T3: build with EXTRA_CFLAGS=-DBRINGUP_WDT_STALL=1 (watchdog stops
 * while the debugger halts the CPU) or =0 (keeps counting). 3 s timeout on
 * the 32768 Hz LF clock, fed every 500 ms loop pass. */
#ifdef BRINGUP_WDT_STALL
#define WDT_TICKS (3U * 32768U)

static void wdtFeed(void)
{
    CKMDUnlockWatchdog();
    CKMDSetWatchdogCounter(WDT_TICKS); /* writing the counter relocks */
}

static void wdtStart(bool stallWhenHalted)
{
    CKMDUnlockWatchdog();
    CKMDSetWatchdogDebugConfig(stallWhenHalted);
    wdtFeed();
}
#endif

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

#ifdef BRINGUP_T5
/* Plan test T5: EXTRA_CFLAGS=-DBRINGUP_T5. Sleeps up to 10 s per pass, holds
 * the green LED (DIO15) on, logs why each wake happened. */
#include <ti/drivers/dpl/SemaphoreP.h>
#include <ti/drivers/dpl/ClockP.h>

#define T5_GREEN_LED_DIO 15
static SemaphoreP_Handle t5Sem;
static volatile uint32_t t5StandbyCount;
static Power_NotifyObj t5NotifyObj;

static int_fast16_t t5StandbyNotify(uint_fast16_t eventType, uintptr_t eventArg, uintptr_t clientArg)
{
    (void)eventType; (void)eventArg; (void)clientArg;
    t5StandbyCount++;
    return Power_NOTIFYDONE;
}
#endif

static void irqCallback(uint_least8_t index)
{
    (void)index;
    irqSeen = true;
    irqCount++;
#ifdef BRINGUP_T5
    SemaphoreP_post(t5Sem);
#endif
}

#ifdef BRINGUP_T5
static void t5Loop(void)
{
    char line[96];
    uint32_t tickUs = ClockP_getSystemTickPeriod();
    uint32_t last = ClockP_getSystemTicks();

    GPIO_setConfig(T5_GREEN_LED_DIO, GPIO_CFG_OUT_STD | GPIO_CFG_OUT_HIGH);
    Power_registerNotify(&t5NotifyObj, PowerLPF3_ENTERING_STANDBY, t5StandbyNotify, 0);
    logStr("T5: sleeping up to 10 s per pass, green LED held on\r\n");

    while (1)
    {
        bool byIrq = SemaphoreP_pend(t5Sem, 10000000U / tickUs) == SemaphoreP_OK;
        uint32_t now = ClockP_getSystemTicks();
        GPIO_toggle(CONFIG_GPIO_LED_HEARTBEAT);
        snprintf(line, sizeof line, "wake: %s  +%lu ms  stby=%lu btn=%u irqs=%lu\r\n",
                 byIrq ? "IRQ    " : "timeout", (unsigned long)((now - last) * (tickUs / 1000U)),
                 (unsigned long)t5StandbyCount, (unsigned)GPIO_read(CONFIG_GPIO_BTN_IRQ),
                 (unsigned long)irqCount);
        logStr(line);
        last = now;
    }
}
#endif

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
#ifdef BRINGUP_WDT_STALL
    wdtStart(BRINGUP_WDT_STALL != 0);
    logStr(BRINGUP_WDT_STALL ? "WDT: 3 s, stall when halted ON\r\n" : "WDT: 3 s, stall when halted OFF\r\n");
#endif

    /* BTN-1 floats on this LaunchPad (the board file's external pull-up is
     * not there in practice: the pin stayed low after the first press).
     * TODO: move the pull-up into boards/launchpad.syscfg via SysConfig. */
    GPIO_setConfig(CONFIG_GPIO_BTN_IRQ, GPIO_CFG_IN_PU | GPIO_CFG_IN_INT_FALLING);
#ifdef BRINGUP_T5
    t5Sem = SemaphoreP_createBinary(0);
#endif
    GPIO_setCallback(CONFIG_GPIO_BTN_IRQ, irqCallback);
    GPIO_enableInt(CONFIG_GPIO_BTN_IRQ);

#ifdef BRINGUP_T5
    t5Loop();
#endif
    uint32_t ticks = 0;
    while (1)
    {
        GPIO_toggle(CONFIG_GPIO_LED_HEARTBEAT);
#ifdef BRINGUP_WDT_STALL
        wdtFeed();
#endif
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
    /* No wake-mask change needed: T5 showed a GPIO edge wakes the chip from
     * Standby at once with TI's stock Power_init (EVTULL WKUPMASK = RTC only). */
    NoRTOS_start();
#ifdef BRINGUP_NO_STANDBY
    Power_setConstraint(PowerLPF3_DISALLOW_STANDBY);
#endif
    mainThread(resetReason);
    return 0;
}
