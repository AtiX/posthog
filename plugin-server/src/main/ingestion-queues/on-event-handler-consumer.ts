import * as schedule from 'node-schedule'

import { KAFKA_EVENTS_JSON, prefix as KAFKA_PREFIX } from '../../config/kafka-topics'
import { Hub } from '../../types'
import { status } from '../../utils/status'
import Piscina from '../../worker/piscina'
import { eachBatchAsyncHandlers } from './batch-processing/each-batch-async-handlers'
import { IngestionConsumer } from './kafka-queue'
import { makeServiceFromKafkaJSConsumer } from './scheduled-tasks-consumer'

export const startOnEventHandlerConsumer = async ({
    hub, // TODO: remove needing to pass in the whole hub and be more selective on dependency injection.
    piscina,
}: {
    hub: Hub
    piscina: Piscina
}) => {
    /*
        Consumes analytics events from the Kafka topic `clickhouse_events_json`
        and processes any onEvent plugin handlers configured for the team. This
        also includes `exportEvents` handlers defined in plugins as these are
        also handled via modifying `onEvent` to call `exportEvents`.

        At the moment this is just a wrapper around `IngestionConsumer`. We may
        want to further remove that abstraction in the future.
    */
    status.info('🔁', 'Starting onEvent handler consumer')

    const queue = buildOnEventIngestionConsumer({ hub, piscina })

    await queue.start()

    schedule.scheduleJob('0 * * * * *', async () => {
        await queue.emitConsumerGroupMetrics()
    })

    // every 5 minutes all ActionManager caches are reloaded for eventual consistency
    schedule.scheduleJob('*/5 * * * *', async () => {
        await piscina?.broadcastTask({ task: 'reloadAllActions' })
    })

    return makeServiceFromKafkaJSConsumer(queue.consumer)
}

export const buildOnEventIngestionConsumer = ({ hub, piscina }: { hub: Hub; piscina: Piscina }) => {
    return new IngestionConsumer(
        hub,
        piscina,
        KAFKA_EVENTS_JSON,
        `${KAFKA_PREFIX}clickhouse-plugin-server-async`,
        eachBatchAsyncHandlers
    )
}
