import { kea, path, actions, reducers, events } from 'kea'
import type { currentPageLogicType } from './currentPageLogicType'

export const currentPageLogic = kea<currentPageLogicType>([
    path(['toolbar', 'stats', 'currentPageLogic']),
    actions(() => ({
        setHref: (href: string) => ({ href }),
        setWildcardHref: (href: string) => ({ href }),
    })),
    reducers(() => ({
        href: [window.location.href, { setHref: (_, { href }) => href }],
        wildcardHref: [
            window.location.href,
            { setHref: (_, { href }) => href, setWildcardHref: (_, { href }) => href },
        ],
    })),
    events(({ actions, cache, values }) => ({
        afterMount: () => {
            cache.interval = window.setInterval(() => {
                if (window.location.href !== values.href) {
                    actions.setHref(window.location.href)
                }
            }, 500)
        },
        beforeUnmount: () => {
            window.clearInterval(cache.interval)
        },
    })),
])
