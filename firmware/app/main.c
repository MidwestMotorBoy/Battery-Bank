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

static void irqCallback(uint_least8_t index)
{
    (void)index;
    irqEdges++;
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

    GPIO_setCallback(CONFIG_GPIO_IRQ_N, irqCallback);
    GPIO_enableInt(CONFIG_GPIO_IRQ_N);

    uint32_t tick = 0;
    uint32_t edgesSeen = 0;
    while (1)
    {
        GPIO_toggle(CONFIG_GPIO_LED_HEARTBEAT);

        uint32_t edges = irqEdges;
        if (edges != edgesSeen)
        {
            logStr("IRQ_N: falling edge(s), total ");
            logUint(edges);
            logStr("\r\n");
            edgesSeen = edges;
        }

        /* Once a second: uptime and the IRQ_N level (a source stuck low
         * would hold it at 0 and cost 70 uA in S2; see rule 3) */
        if ((++tick & 1) == 0)
        {
            logStr("t=");
            logUint(tick / 2);
            logStr("s IRQ_N=");
            logUint(GPIO_read(CONFIG_GPIO_IRQ_N));
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
    NoRTOS_start();
    mainThread(resetReason);
    return 0;
}
