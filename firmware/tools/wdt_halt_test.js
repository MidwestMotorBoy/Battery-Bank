// T3: halt the CPU for 10 s (watchdog timeout is 3 s), then let it run.
// Run: C:/ti/ccs2101/ccs/scripting/run.bat firmware/tools/wdt_halt_test.js (plan test T3)
// Reads WDTCNT (CKMD 0x40001300) and WDTTEST (0x40001304) while halted.
const sleep = ms => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
const WDTCNT = 0x40001300, WDTTEST = 0x40001304;
const t = () => new Date().toISOString().slice(11, 23);
const ds = initScripting();
ds.setScriptingTimeout(30000);
ds.configure("C:/Users/Logan/Documents/BatteryBank/firmware/targets/lp_em_cc2340r53_xds110.ccxml");
const session = ds.openSession(/cortex/i);
session.target.connect();
if (!session.target.isHalted()) session.target.halt();
const rd = a => Number(session.memory.readOne(a, 32));
console.log(t(), "halted. WDTTEST.STALLEN =", rd(WDTTEST) & 1, " WDTCNT =", rd(WDTCNT));
for (let i = 1; i <= 5; i++) {
    sleep(2000);
    let msg;
    try { msg = `halted=${session.target.isHalted()} WDTCNT=${rd(WDTCNT)}`; }
    catch (e) { msg = "read failed: " + e.message; }
    console.log(t(), `+${2 * i}s`, msg);
}
try { session.target.run(false); console.log(t(), "resumed"); }
catch (e) { console.log(t(), "run failed: " + e.message); }
session.target.disconnect();
ds.shutdown?.();
