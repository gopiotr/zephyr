# SPDX-License-Identifier: Apache-2.0

set(ENV{QEMU_BIN_PATH} /home/redbeard/Nordic/qemu/build/arm)

set(EMU_PLATFORM qemu)

set(QEMU_CPU_TYPE_${ARCH} cortex-m4)
set(QEMU_FLAGS_${ARCH}
  -cpu ${QEMU_CPU_TYPE_${ARCH}}
  -machine nRF52840DK
  -nographic
  -vga none
  )

board_set_debugger_ifnset(qemu)
