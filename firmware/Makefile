# MonolithDev MCU firmware: CC2340R5MODA on the dev board, CC2340R53 on the
# LP-EM-CC2340R53 LaunchPad for bring-up. Run from Git Bash with gmake.
#
#   make                  build for the LaunchPad (BOARD=launchpad)
#   make flash            flash over the XDS110 with DSLite
#   make gui              open the pin/peripheral config in the SysConfig GUI
#   make clean
#
# Layout follows TI's SDK example makefiles: SysConfig generates the driver
# config, the CCFG and the linker includes into build/<board>/syscfg.

-include tools.mak
ifeq ($(SDK),)
    $(error tools.mak missing: copy tools.mak.example to tools.mak and set the paths)
endif

BOARD   ?= launchpad
NAME    := batterybank_$(BOARD)
BUILD   := build/$(BOARD)
GEN     := $(BUILD)/syscfg
SYSCFG  := boards/$(BOARD).syscfg

CC      := "$(TICLANG_ARMCOMPILER)/bin/tiarmclang"
OBJCOPY := "$(TICLANG_ARMCOMPILER)/bin/tiarmobjcopy"
SYSCFG_CMD := "$(SYSCONFIG_TOOL)" --compiler ticlang --product "$(SDK)/.metadata/product.json"

# Ask SysConfig which files it will generate (TI does the same at parse time)
SYSCFG_FILES := $(shell $(SYSCFG_CMD) --listGeneratedFiles --listReferencedFiles --output $(GEN) $(SYSCFG))
SYSCFG_C_FILES   := $(filter %.c,$(SYSCFG_FILES))
SYSCFG_H_FILES   := $(filter %.h,$(SYSCFG_FILES))
SYSCFG_OPT_FILES := $(filter %.opt,$(SYSCFG_FILES))

APP_SRCS := $(wildcard app/*.c)
OBJS := $(addprefix $(BUILD)/,$(notdir $(APP_SRCS:.c=.obj))) \
        $(addprefix $(BUILD)/,$(notdir $(SYSCFG_C_FILES:.c=.obj)))

CFLAGS := -mcpu=cortex-m0plus -march=thumbv6m -mfloat-abi=soft -mthumb \
          -Oz -gdwarf-3 -Wall -std=c11 \
          -I app -I $(GEN) \
          $(addprefix @,$(SYSCFG_OPT_FILES)) \
          -I "$(SDK)/source" \
          -I "$(SDK)/kernel/nortos" \
          -I "$(SDK)/kernel/nortos/posix" \
          -I "$(SDK)/source/ti/posix/ticlang" \
          -DDeviceFamily_CC23X0R5

LFLAGS := -Wl,-i"$(SDK)/source" -Wl,-i"$(SDK)/kernel/nortos" -Wl,-i$(GEN) \
          -Wl,-l,ti_utils_build_linker.cmd.genlibs \
          -Wl,-l,"$(SDK)/source/ti/boards/lpf3/lpf3_nortos.cmd" \
          -Wl,-m,$(BUILD)/$(NAME).map -Wl,--rom_model -Wl,--warn_sections \
          -Wl,--reread_libs -L"$(TICLANG_ARMCOMPILER)/lib" -llibc.a

.PHONY: all flash gui clean

all: $(BUILD)/$(NAME).out $(BUILD)/$(NAME).hex

$(SYSCFG_C_FILES) $(SYSCFG_H_FILES) $(SYSCFG_OPT_FILES) &: $(SYSCFG)
	@echo "SysConfig: $<"
	@$(SYSCFG_CMD) --output $(GEN) $<

$(BUILD)/%.obj: app/%.c $(SYSCFG_H_FILES) $(SYSCFG_OPT_FILES) | $(BUILD)
	@echo "CC  $<"
	@$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.obj: $(GEN)/%.c $(SYSCFG_H_FILES) $(SYSCFG_OPT_FILES) | $(BUILD)
	@echo "CC  $<"
	@$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/$(NAME).out: $(OBJS)
	@echo "LD  $@"
	@$(CC) $(CFLAGS) $(OBJS) $(LFLAGS) -o $@

$(BUILD)/$(NAME).hex: $(BUILD)/$(NAME).out
	@$(OBJCOPY) -O ihex $< $@

$(BUILD):
	@mkdir -p $@

flash: $(BUILD)/$(NAME).out
	"$(DSLITE)" load -c $(CCXML) -f $< -e

# Open the board's .syscfg in the SysConfig GUI (pins, peripherals, CCFG).
# Save there, then run make: the build regenerates from the saved file.
gui:
	cmd //c start "" "$(subst /,\,$(dir $(SYSCONFIG_TOOL)))sysconfig_gui.bat" \
	    --product "$(subst /,\,$(SDK))\.metadata\product.json" \
	    --compiler ticlang "$(subst /,\,$(abspath $(SYSCFG)))"

clean:
	rm -rf build
