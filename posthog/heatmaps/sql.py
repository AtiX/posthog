from django.conf import settings

from posthog.clickhouse.kafka_engine import kafka_engine
from posthog.clickhouse.table_engines import (
    Distributed,
    ReplicationScheme,
    MergeTreeEngine,
)
from posthog.kafka_client.topics import KAFKA_CLICKHOUSE_HEATMAP_EVENTS

HEATMAPS_DATA_TABLE = lambda: "sharded_heatmaps"


"""
We intend to send specific $heatmap events to build a heatmap instead of building from autocapture like the click map
We'll be storing individual clicks per url/team/session
And we'll be querying for those clicks at day level of granularity
And we'll be querying by URL exact or wildcard match
And we'll _sometimes_ be querying by width

We _could_ aggregate this data by day, but we're hoping this will be small/fast enough not to bother
And can always add a materialized view for day (and week?) granularity driven by this data if needed

We only add session_id so that we could offer example sessions for particular clicked areas in the toolbar
"""

KAFKA_HEATMAPS_TABLE_BASE_SQL = """
CREATE TABLE IF NOT EXISTS {table_name} ON CLUSTER '{cluster}'
(
    $session_id VARCHAR,
    team_id Int64,
    timestamp DateTime64(6, 'UTC'),
    -- x is the x with resolution applied, the resolution converts high fidelity mouse positions into an NxN grid
    x Int16,
    -- y is the y with resolution applied, the resolution converts high fidelity mouse positions into an NxN grid
    y Int16,
    -- stored so that in future we can support other resolutions
    scale_factor Int16,
    $viewport_width Int16,
    $viewport_height Int16,
    -- some elements move when the page scrolls, others do not
    $pointer_target_fixed Bool,
    $current_url VARCHAR
) ENGINE = {engine}
"""

HEATMAPS_TABLE_BASE_SQL = """
CREATE TABLE IF NOT EXISTS {table_name} ON CLUSTER '{cluster}'
(
    $session_id VARCHAR,
    team_id Int64,
    timestamp DateTime64(6, 'UTC'),
    -- x is the x with resolution applied, the resolution converts high fidelity mouse positions into an NxN grid
    x Int16,
    -- y is the y with resolution applied, the resolution converts high fidelity mouse positions into an NxN grid
    y Int16,
    -- stored so that in future we can support other resolutions
    scale_factor Int16,
    $viewport_width Int16,
    $viewport_height Int16,
    -- some elements move when the page scrolls, others do not
    $pointer_target_fixed Bool,
    $current_url VARCHAR,
    _timestamp DateTime
) ENGINE = {engine}
"""

HEATMAPS_DATA_TABLE_ENGINE = lambda: MergeTreeEngine("heatmaps", replication_scheme=ReplicationScheme.SHARDED)

HEATMAPS_TABLE_SQL = lambda: (
    HEATMAPS_TABLE_BASE_SQL
    + """
    PARTITION BY toYYYYMM(timestamp)
    -- almost always this is being queried by
    --   * team_id,
    --   * date range,
    --   * URL (maybe matching wild cards),
    --   * width
    -- we'll almost never query this by session id
    -- so from least to most cardinality that's
    ORDER BY (team_id,  toDate(timestamp), $current_url, $viewport_width)
-- I am purposefully not setting index granularity
-- the default is 8192, and we will be loading a lot of data
-- per query, we tend to copy this 512 around the place but
-- i don't think it applies here
"""
).format(
    table_name=HEATMAPS_DATA_TABLE(),
    cluster=settings.CLICKHOUSE_CLUSTER,
    engine=HEATMAPS_DATA_TABLE_ENGINE(),
)

KAFKA_HEATMAPS_TABLE_SQL = lambda: KAFKA_HEATMAPS_TABLE_BASE_SQL.format(
    table_name="kafka_heatmaps",
    cluster=settings.CLICKHOUSE_CLUSTER,
    engine=kafka_engine(topic=KAFKA_CLICKHOUSE_HEATMAP_EVENTS),
)

HEATMAPS_TABLE_MV_SQL = (
    lambda: """
CREATE MATERIALIZED VIEW IF NOT EXISTS heatmaps_mv ON CLUSTER '{cluster}'
TO {database}.{target_table}
AS SELECT
    $session_id,
    team_id,
    timestamp,
    -- x is the x with resolution applied, the resolution converts high fidelity mouse positions into an NxN grid
    x,
    -- y is the y with resolution applied, the resolution converts high fidelity mouse positions into an NxN grid
    y,
    -- stored so that in future we can support other resolutions
    scale_factor,
    $viewport_width,
    $viewport_height,
    -- some elements move when the page scrolls, others do not
    $pointer_target_fixed,
    $current_url
FROM {database}.kafka_heatmaps
""".format(
        target_table="writable_heatmaps",
        cluster=settings.CLICKHOUSE_CLUSTER,
        database=settings.CLICKHOUSE_DATABASE,
    )
)

# Distributed engine tables are only created if CLICKHOUSE_REPLICATED

# This table is responsible for writing to sharded_heatmaps based on a sharding key.
WRITABLE_HEATMAPS_TABLE_SQL = lambda: HEATMAPS_TABLE_BASE_SQL.format(
    table_name="writable_heatmaps",
    cluster=settings.CLICKHOUSE_CLUSTER,
    engine=Distributed(
        data_table=HEATMAPS_DATA_TABLE(),
        # I don't think there's a great natural sharding key here
        # we'll be querying for team data by url and date,
        # so I _think_ this offers a reasonable spread of write load
        # without needing to query too many shards
        sharding_key="cityHash64(concat(toString(team_id), '-', $current_url, '-', toString(toDate(timestamp))))",
    ),
)

# This table is responsible for reading from heatmaps on a cluster setting
DISTRIBUTED_HEATMAPS_TABLE_SQL = lambda: HEATMAPS_TABLE_BASE_SQL.format(
    table_name="heatmaps",
    cluster=settings.CLICKHOUSE_CLUSTER,
    engine=Distributed(
        data_table=HEATMAPS_DATA_TABLE(),
        # I don't think there's a great natural sharding key here
        # we'll be querying for team data by url and date,
        # so I _think_ this offers a reasonable spread of write load
        # without needing to query too many shards
        sharding_key="cityHash64(concat(toString(team_id), '-', $current_url, '-', toString(toDate(timestamp))))",
    ),
)

DROP_HEATMAPS_TABLE_SQL = lambda: (
    f"DROP TABLE IF EXISTS {HEATMAPS_DATA_TABLE()} ON CLUSTER '{settings.CLICKHOUSE_CLUSTER}'"
)

TRUNCATE_HEATMAPS_TABLE_SQL = lambda: (
    f"TRUNCATE TABLE IF EXISTS {HEATMAPS_DATA_TABLE()} ON CLUSTER '{settings.CLICKHOUSE_CLUSTER}'"
)
