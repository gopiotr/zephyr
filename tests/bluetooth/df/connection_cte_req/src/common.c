/*
 * Copyright (c) 2021 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr.h>
#include <stddef.h>
#include <ztest.h>

#include <util/util.h>
#include <util/memq.h>

#include <hal/ccm.h>

#include <pdu.h>
#include <lll.h>
#include <lll/lll_df_types.h>
#include <lll_conn.h>

#include <ull_conn_types.h>
#include <ull_conn_internal.h>

#define PEER_FEATURES_ARE_VALID 1U

uint16_t common_create_connection(void)
{
	struct ll_conn *conn;

	conn = ll_conn_acquire();
	zassert_not_equal(conn, NULL, "Failed acquire ll_conn instance");

	conn->lll.latency = 0;
	conn->lll.handle = ll_conn_handle_get(conn);

	return conn->lll.handle;
}

void common_destroy_connection(uint16_t handle)
{
	struct ll_conn *conn;

	conn = ll_conn_get(handle);
	zassert_not_equal(conn, NULL, "Failed ll_conn instance for given handle");

	ll_conn_release(conn);
}

void common_set_peer_features(uint16_t conn_handle, uint64_t features)
{
	struct ll_conn *conn;

	conn = ll_conn_get(conn_handle);
	zassert_not_equal(conn, NULL, "Failed ll_conn instance for given handle");

	conn->common.fex_valid = PEER_FEATURES_ARE_VALID;
	conn->llcp_feature.features_peer = features;
}

void common_set_slave_latency(uint16_t conn_handle, uint16_t slave_latency)
{
	struct ll_conn *conn;

	conn = ll_conn_get(conn_handle);
	zassert_not_equal(conn, NULL, "Failed ll_conn instance for given handle");

	conn->lll.latency = slave_latency;
}
