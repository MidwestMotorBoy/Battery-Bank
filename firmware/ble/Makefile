# BLE build (plan test T6 onwards): TI's basic_ble example, copied unchanged
# from the LPF3 SDK into basic_ble/ and built with TI's own makefile, with
# the tool paths from ../tools.mak. Run from Git Bash in firmware/:
#
#   gmake -C ble          build basic_ble/freertos/ticlang/basic_ble.out
#   gmake -C ble flash    flash it over the XDS110
#   gmake -C ble gui      open basic_ble.syscfg in the SysConfig GUI
#   gmake -C ble clean

include ../tools.mak

TIDIR := basic_ble/freertos/ticlang
TIMAKE := $(MAKE) -C $(TIDIR) SIMPLELINK_LOWPOWER_F3_SDK_INSTALL_DIR=$(SDK) \
          SYSCONFIG_TOOL=$(SYSCONFIG_TOOL) TICLANG_ARMCOMPILER=$(TICLANG_ARMCOMPILER)

.PHONY: all flash gui clean
all:
	$(TIMAKE) -j8

flash: all
	"$(DSLITE)" load -c ../$(CCXML) -f $(TIDIR)/basic_ble.out

gui:
	cmd //c start "" "$(subst /,\,$(dir $(SYSCONFIG_TOOL)))sysconfig_gui.bat" \
	    --product "$(subst /,\,$(SDK))\.metadata\product.json" \
	    --compiler ticlang "$(subst /,\,$(abspath basic_ble/freertos/basic_ble.syscfg))"

clean:
	$(TIMAKE) clean
