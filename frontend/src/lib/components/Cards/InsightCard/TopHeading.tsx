import { dateFilterToText } from 'lib/utils'
import { INSIGHT_TYPES_METADATA, InsightTypeMetadata, QUERY_TYPES_METADATA } from 'scenes/saved-insights/SavedInsights'

import {
    containsHogQLQuery,
    dateRangeFor,
    isDataTableNode,
    isInsightQueryNode,
    isInsightVizNode,
} from '~/queries/utils'
import { InsightType, QueryBasedInsightModel } from '~/types'

export function TopHeading({ insight }: { insight: QueryBasedInsightModel }): JSX.Element {
    const { query } = insight

    let insightType: InsightTypeMetadata

    if (query?.kind) {
        if ((isDataTableNode(query) && containsHogQLQuery(query)) || isInsightVizNode(query)) {
            insightType = QUERY_TYPES_METADATA[query.source.kind]
        } else {
            insightType = QUERY_TYPES_METADATA[query.kind]
        }
    } else {
        // maintain the existing default
        insightType = INSIGHT_TYPES_METADATA[InsightType.TRENDS]
    }

    let date_from, date_to
    if (query) {
        const queryDateRange = dateRangeFor(query)
        if (queryDateRange) {
            date_from = queryDateRange.date_from
            date_to = queryDateRange.date_to
        }
    }

    let dateText: string | null = null
    if (insightType?.name !== 'Retention') {
        const defaultDateRange =
            query == undefined || isInsightQueryNode(query) || isInsightVizNode(query) ? 'Last 7 days' : null
        dateText = dateFilterToText(date_from, date_to, defaultDateRange)
    }
    return (
        <>
            <span title={insightType?.description}>{insightType?.name}</span>
            {dateText ? <> • {dateText}</> : null}
        </>
    )
}
