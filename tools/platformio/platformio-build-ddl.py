"""
HC32F46x DDL
Device Driver Libraries for the HC32F46x series of microcontrollers
"""
import os
import re
from os.path import isdir, join

from SCons.Script import DefaultEnvironment

print("platformio-build-ddl.py running")

# get the environment
env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
build_core = board.get("build.core", "")

# ensure framework is installed
FRAMEWORK_DIR = platform.get_package_dir("framework-hc32f46x-ddl")
DDL_DIR = join(FRAMEWORK_DIR, "cores", "ddl")
assert isdir(DDL_DIR)

# find and print ddl version from version.txt
def get_ddl_version(version_file: str) -> str:
    with open(version_file, "r") as f:
        for line in f.readlines():
            if re.match(r"\d+\.\d+\.\d+", line):
                return line.split()[0]
    
    return "unknown"
ddl_version = get_ddl_version(join(DDL_DIR, "version.txt"))
print(f"Using DDL version {ddl_version}")

# prepare basic compile environment
# as far as i understood, the flags in 'CCFLAGS' should be added to all the other flags, but it doesn't seem to work that way...
# as such, i'm adding them to all the other flags manually, which is kinda hacky, but seems to work just fine
common_gcc_flags = [
    "-mcpu=cortex-m4",
	"-mthumb",
	"-mthumb-interwork",
	"-Os",
	"-fmessage-length=0",
	"-fsigned-char",
	"-ffunction-sections",
	"-fdata-sections",
	"-Wall",
	"-g"
]
env.Append(
    # common gcc (?)
    CCFLAGS=common_gcc_flags + [],

    # c
    CFLAGS=common_gcc_flags + [
        "-std=gnu17"
    ],
    
    # c++
    CXXFLAGS=common_gcc_flags + [
        "-std=gnu++17",
        "-fabi-version=0"
    ],

    # asm
    ASFLAGS=common_gcc_flags + [
        "-x", "assembler-with-cpp"
    ],

    # linker
    LINKFLAGS=common_gcc_flags + [
        "-Xlinker",
        "--gc-sections",
        ("-Wl,--default-script", board.get("build.ldscript", join(FRAMEWORK_DIR, "ld", "hc32f46x_param.ld"))),
        #"-Wl,--no-warn-rwx-segment", # introduced in gcc 12, and thus not supported by the version platformio uses
        "-Wl,--print-memory-usage",
        "--specs=nano.specs",
        "--specs=nosys.specs",
    ],

    # c/c++ defines
    CPPDEFINES=[
        "HC32F460",
        "USE_DEVICE_DRIVER_LIB",
        "__TARGET_FPU_VFP",
	    "__FPU_PRESENT=1",
	    "_MPU_PRESENT=1",
	    "ARM_MATH_CM4",
	    "ARM_MATH_MATRIX_CHECK",
	    "ARM_MATH_ROUNDING"
    ],

    # c/c++ include paths
    # all directories in core/ddl are added to the include path
    CPPPATH=[
        DDL_DIR,
        join(DDL_DIR, "addon"),
        join(DDL_DIR, "cmsis"),
        join(DDL_DIR, "common"),
        join(DDL_DIR, "compat"),
        join(DDL_DIR, "library", "inc"),
        join(DDL_DIR, "startup"),
    ]
)


# resolve and append linker script parameters to ld command line
# parameters are passed into the linker script via the --defsym flag, as symbols
# this allows the linker script to be generic, and the parameters to be passed in using the board manifest
# however, this could cause issues as it's not *exactly* what this flag is for, but it should work for a while...
def get_ld_params():
    # define keys to symbol def names
    ld_args = []
    ld_arg_keys_to_def_mapping = {
        "build.ld_args.flash_start": "FLASH_START",
        "build.ld_args.flash_size": "FLASH_SIZE",
    }

    # get all the keys from the board manifest, append to arguments list
    for key, def_name in ld_arg_keys_to_def_mapping.items():
        if key in board:
            print("linker script param {0} = {1}".format(def_name, board.get(key)))
            ld_args.append("-Wl,--defsym={0}={1}".format(def_name, board.get(key)))
    
    return ld_args

env.Append(LINKFLAGS=get_ld_params())


# resolve and append ddl configuration to defines
# ddl configuration is defined in the board manifest, as a way to enable additional drivers
def get_ddl_config_defines():
    # ddl config key to define mapping
    ddl_config_defines = []
    ddl_config_keys_to_def_mapping = {
        "build.ddl.print" : "DDL_PRINT_ENABLE",
        "build.ddl.adc" : "DDL_ADC_ENABLE", 
        "build.ddl.aes" : "DDL_AES_ENABLE", 
        "build.ddl.can" : "DDL_CAN_ENABLE", 
        "build.ddl.cmp" : "DDL_CMP_ENABLE", 
        "build.ddl.clk" : "DDL_CLK_ENABLE",
        "build.ddl.crc" : "DDL_CRC_ENABLE", 
        "build.ddl.dcu" : "DDL_DCU_ENABLE", 
        "build.ddl.dmac" : "DDL_DMAC_ENABLE", 
        "build.ddl.efm" : "DDL_EFM_ENABLE", 
        "build.ddl.emb" : "DDL_EMB_ENABLE", 
        "build.ddl.event_port": "DDL_EVENT_PORT_ENABLE",
        "build.ddl.extint" : "DDL_EXINT_NMI_SWI_ENABLE", 
        "build.ddl.gpio" : "DDL_GPIO_ENABLE", 
        "build.ddl.hash" : "DDL_HASH_ENABLE", 
        "build.ddl.i2c" : "DDL_I2C_ENABLE", 
        "build.ddl.i2s" : "DDL_I2S_ENABLE", 
        "build.ddl.interrupts" : "DDL_INTERRUPTS_ENABLE", 
        "build.ddl.interrupts_share": "DDL_INTERRUPTS_SHARE_ENABLE",
        "build.ddl.keyscan" : "DDL_KEYSCAN_ENABLE", 
        "build.ddl.mpu" : "DDL_MPU_ENABLE", 
        "build.ddl.ots" : "DDL_OTS_ENABLE", 
        "build.ddl.pga" : "DDL_PGA_ENABLE", 
        "build.ddl.pwc" : "DDL_PWC_ENABLE", 
        "build.ddl.qspi" : "DDL_QSPI_ENABLE", 
        "build.ddl.rmu" : "DDL_RMU_ENABLE", 
        "build.ddl.rtc" : "DDL_RTC_ENABLE", 
        "build.ddl.sdioc" : "DDL_SDIOC_ENABLE", 
        "build.ddl.spi" : "DDL_SPI_ENABLE", 
        "build.ddl.sram" : "DDL_SRAM_ENABLE", 
        "build.ddl.swdt" : "DDL_SWDT_ENABLE", 
        "build.ddl.timer0" : "DDL_TIMER0_ENABLE", 
        "build.ddl.timer4.cnt" : "DDL_TIMER4_CNT_ENABLE", 
        "build.ddl.timer4.emb" : "DDL_TIMER4_EMB_ENABLE", 
        "build.ddl.timer4.oco" : "DDL_TIMER4_OCO_ENABLE", 
        "build.ddl.timer4.pwm" : "DDL_TIMER4_PWM_ENABLE", 
        "build.ddl.timer4.sevt" : "DDL_TIMER4_SEVT_ENABLE",
        "build.ddl.timer6" : "DDL_TIMER6_ENABLE", 
        "build.ddl.timera" : "DDL_TIMERA_ENABLE", 
        "build.ddl.trng" : "DDL_TRNG_ENABLE", 
        "build.ddl.usart" : "DDL_USART_ENABLE", 
        "build.ddl.usbfs" : "DDL_USBFS_ENABLE", 
        "build.ddl.wdt" : "DDL_WDT_ENABLE", 
    }

    # get all the keys from the board manifest, append to arguments list
    for key, def_name in ddl_config_keys_to_def_mapping.items():
        if board.get(key, "false") == "true":
            print("Driver Library '{0}' enabled".format(def_name))
            ddl_config_defines.append(def_name)
    
    # return list without duplicates
    return list(dict.fromkeys(ddl_config_defines))


# add ddl config defines to defines
env.Append(CPPDEFINES=get_ddl_config_defines())


# resolve middleware configuration and build
# middleware configuration is defined in the board manifest, just like ddl configuration
# however, middleware is not just a list of defines, but instead a change in the include paths and source files
MW_DIR = join(FRAMEWORK_DIR, "middleware")
if isdir(MW_DIR):
    # find all available middleware, by folder name
    for mw in [f.name for f in os.scandir(MW_DIR) if f.is_dir()]: # [sd_card, w25q]
        # check if middleware is enabled in the board manifest
        if board.get("build.mw." + mw, "false") == "true":
            print("Middleware '{0}' enabled".format(mw))

            # add middleware include paths to the build
            env.Append(CPPPATH=[join(MW_DIR, mw, "inc")])

            # build middleware
            env.BuildSources(join("$BUILD_DIR", "FrameworkDDL_" + mw), join(MW_DIR, mw, "src"))

# build ddl core
env.BuildSources(join("$BUILD_DIR", "FrameworkDDL"), DDL_DIR)
