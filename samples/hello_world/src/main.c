/*
 * Copyright (c) 2012-2014 Wind River Systems, Inc.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr.h>
#include <sys/printk.h>
#include <timing/timing.h>

void main(void)
{
	timing_t start_time, end_time;
	uint64_t total_cycles;
	uint64_t total_ns;

	timing_init();
	timing_start();

	start_time = timing_counter_get();

	k_busy_wait(10000000); // 10 sec

	end_time = timing_counter_get();

	total_cycles = timing_cycles_get(&start_time, &end_time);
	total_ns = timing_cycles_to_ns(total_cycles);

	printk("Elapsed time: %lld [cycles] | %lld [ns]\n", total_cycles, total_ns);

	timing_stop();

	printk("Hello World! %s\n", CONFIG_BOARD);
}
