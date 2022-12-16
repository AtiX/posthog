import { useEffect, useState } from 'react'
import { BindLogic, useActions, useValues } from 'kea'
import clsx from 'clsx'

import { insightLogic } from 'scenes/insights/insightLogic'
import { insightSceneLogic } from 'scenes/insights/insightSceneLogic'
import { InsightsNav } from 'scenes/insights/InsightsNav'
import { InsightContainer } from 'scenes/insights/InsightContainer'
import { ItemMode } from '~/types'
import { isFunnelsQuery } from '~/queries/utils'

import { dataNodeLogic, DataNodeLogicProps } from '../DataNode/dataNodeLogic'
import { queryNodeToFilter } from '../InsightQuery/queryNodeToFilter'
import { InsightQueryNode, InsightVizNode } from '../../schema'

import { EditorFilters } from './EditorFilters'

type InsightVizProps = {
    query: InsightVizNode
    setQuery?: (node: InsightVizNode) => void
}

let uniqueNode = 0

export function InsightViz({ query, setQuery }: InsightVizProps): JSX.Element {
    const [key] = useState(() => `InsightViz.${uniqueNode++}`)

    const dataNodeLogicProps: DataNodeLogicProps = { query: query.source, key }
    const { response, lastRefresh } = useValues(dataNodeLogic(dataNodeLogicProps))

    const { insight } = useValues(insightLogic)
    const { setInsight, setLastRefresh } = useActions(insightLogic)
    const { insightMode } = useValues(insightSceneLogic) // TODO: Tight coupling -- remove or make optional

    // TODO: use connected logic instead of useEffect?
    useEffect(() => {
        if (response) {
            setInsight(
                {
                    ...insight,
                    result: response.result,
                    next: response.next,
                    timezone: response.timezone,
                    filters: queryNodeToFilter(query.source),
                },
                {}
            )
            setLastRefresh(lastRefresh)
        }
    }, [response])

    const isFunnels = isFunnelsQuery(query.source)

    const setQuerySource = (source: InsightQueryNode): void => {
        setQuery?.({ ...query, source })
    }

    return (
        // <BindLogic logic={dataTableLogic} props={dataTableLogicProps}>
        <BindLogic logic={dataNodeLogic} props={dataNodeLogicProps}>
            {insightMode === ItemMode.Edit && <InsightsNav />}
            <div
                className={clsx('insight-wrapper', {
                    'insight-wrapper--singlecolumn': isFunnels,
                })}
            >
                <EditorFilters query={query.source} setQuery={setQuerySource} />

                <div>
                    <h4>Query</h4>
                    <pre>{JSON.stringify(query, null, 2)}</pre>
                </div>

                <div className="insights-container" data-attr="insight-view">
                    <InsightContainer insightMode={insightMode} />
                </div>
            </div>
        </BindLogic>
        // </BindLogic>
    )
}
