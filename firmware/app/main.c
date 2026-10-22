/*
 * MonolithDev MCU firmware, bring-up skeleton (NoRTOS).
 *
 * Builds for the LP-EM-CC2340R53 LaunchPad (BOARD=launchpad) and the dev
 * board (BOARD=devboard). Proves the build, the probe and the UART:
 * - drives every dev-board output to its safe state before anything else
 *   (CHG_INH high, EN_5V1/EN_5V2 low, 3V3_SLEEP high; mcu-io-power-states.md
 *   rule 7)
 * - prints a banner and the reset reason on the log UART (115200 8N1)
 * - blinks the heartbeat LED at 1 Hz
 * - logs each falling edge on IRQ_N (BTN-1 on the LaunchPad) and, on the
 *   dev board, the level of IRQ_N every second so a stuck-low source shows
 * Plan-test builds (EXTRA_CFLAGS=...): -DBRINGUP_WDT_STALL=0/1 (T3),
 * -DBRINGUP_T5 (T5), -DBRINGUP_NO_STANDBY.
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
static volatile uint32_t irqEdges;

static void logStr(const char *s)
{
    UART2_write(uartLog, s, strlen(s), NULL);
}

static void logUint(uint32_t v)
{
    char buf[11];
    int i = sizeof(buf) - 1;
    buf[i] = '\0';
    do
    {
        buf[--i] = (char)('0' + v % 10);
        v /= 10;
    } while (v && i);
    logStr(&buf[i]);
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
    irqEdges++;
#ifdef BRINGUP_T5
    SemaphoreP_post(t5Sem);
#endif
}

/*
 * Safe outputs. SysConfig already sets the initial levels, so this is belt
 * and braces: it is the first thing main() does after Board_init(), and it
 * is where the EN_5Vx restore-from-retained-RAM goes later (review 4 C-6).
 */
static void outputsSafe(void)
{
#ifdef CONFIG_GPIO_CHG_INH
    GPIO_write(CONFIG_GPIO_CHG_INH, 1);     /* charging inhibited */
#endif
#ifdef CONFIG_GPIO_EN_5V1
    GPIO_write(CONFIG_GPIO_EN_5V1, 0);      /* PP5V off */
#endif
#ifdef CONFIG_GPIO_EN_5V2
    GPIO_write(CONFIG_GPIO_EN_5V2, 0);
#endif
#ifdef CONFIG_GPIO_3V3_SLEEP
    GPIO_write(CONFIG_GPIO_3V3_SLEEP, 1);   /* TPS62177 normal mode */
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
        snprintf(line, sizeof line, "wake: %s  +%lu ms  stby=%lu IRQ_N=%u irqs=%lu\r\n",
                 byIrq ? "IRQ    " : "timeout", (unsigned long)((now - last) * (tickUs / 1000U)),
                 (unsigned long)t5StandbyCount, (unsigned)GPIO_read(CONFIG_GPIO_IRQ_N),
                 (unsigned long)irqEdges);
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
    logStr("Board: " BOARD_NAME "\r\n");
    logStr("Built " __DATE__ " " __TIME__ "\r\n");
    logStr("Reset reason: ");
    logStr(resetReasonName(resetReason));
    logStr("\r\n");
#ifdef BRINGUP_WDT_STALL
    wdtStart(BRINGUP_WDT_STALL != 0);
    logStr(BRINGUP_WDT_STALL ? "WDT: 3 s, stall when halted ON\r\n" : "WDT: 3 s, stall when halted OFF\r\n");
#endif

#ifdef BOARD_launchpad
    /* BTN-1 floats on this LaunchPad (the board file's external pull-up is
     * not there in practice: the pin stayed low after the first press).
     * The dev board has its own pull-up on IRQ_N, so its internal pull stays off.
     * TODO: move the pull-up into boards/launchpad.syscfg via SysConfig. */
    GPIO_setConfig(CONFIG_GPIO_IRQ_N, GPIO_CFG_IN_PU | GPIO_CFG_IN_INT_FALLING);
#endif
#ifdef BRINGUP_T5
    t5Sem = SemaphoreP_createBinary(0);
#endif
    GPIO_setCallback(CONFIG_GPIO_IRQ_N, irqCallback);
    GPIO_enableInt(CONFIG_GPIO_IRQ_N);

#ifdef BRINGUP_T5
    t5Loop();
#endif
    uint32_t tick = 0;
    uint32_t edgesSeen = 0;
    while (1)
    {
        GPIO_toggle(CONFIG_GPIO_LED_HEARTBEAT);
#ifdef BRINGUP_WDT_STALL
        wdtFeed();
#endif

        uint32_t edges = irqEdges;
        if (edges != edgesSeen)
        {
            logStr("IRQ_N: falling edge(s), total ");
            logUint(edges);
            logStr("\r\n");
            edgesSeen = edges;
        }

        /* Once a second: uptime, the IRQ_N level (a source stuck low
         * would hold it at 0 and cost 70 uA in S2; see rule 3), and the reset
         * reason again (the banner is gone before a terminal can reconnect
         * after a power cycle) */
        if ((++tick & 1) == 0)
        {
            logStr("t=");
            logUint(tick / 2);
            logStr("s IRQ_N=");
            logUint(GPIO_read(CONFIG_GPIO_IRQ_N));
            logStr(" rst=");
            logStr(resetReasonName(resetReason));
            logStr("\r\n");
        }

        usleep(500000);
    }
}

int main(void)
{
    /* Read before anything else can disturb the reset status */
    uint32_t resetReason = PMCTLGetResetReason();

    Board_init();
    outputsSafe();
    /* No wake-mask change needed: T5 showed a GPIO edge wakes the chip from
     * Standby at once with TI's stock Power_init (EVTULL WKUPMASK = RTC only). */
    NoRTOS_start();
#ifdef BRINGUP_NO_STANDBY
    Power_setConstraint(PowerLPF3_DISALLOW_STANDBY);
#endif
    mainThread(resetReason);
    return 0;
}
