import { afterMount, kea, path, reducers, selectors } from 'kea'
import { loaders } from 'kea-loaders'
import { router } from 'kea-router'
import api from 'lib/api'
import { toParams } from 'lib/utils'

import type { clientAuthorizationSceneLogicType } from './clientAuthorizationSceneLogicType'

export type AuthenticationFlowInformation = {
    name?: string
    code?: string
    redirect_url?: string
    verification?: string
}

export type AuthenticationFlowResponse = {
    status?: string
    code?: string
    verification?: string
}

export const clientAuthorizationSceneLogic = kea<clientAuthorizationSceneLogicType>([
    path(['scenes', 'authorization', 'clientAuthorizationSceneLogic']),

    reducers({
        completed: [
            false,
            {
                confirmAndRedirectSuccess: () => true,
            },
        ],
    }),

    loaders(({ values }) => ({
        authentication: [
            null as AuthenticationFlowInformation | null,
            {
                loadAuthenticationFlow: async () => {
                    const code = router.values.searchParams['code']
                    const clientId = router.values.searchParams['client_id']
                    const redirectUrl = router.values.searchParams['redirect_url']

                    if (!clientId) {
                        throw new Error('Missing client_id')
                    }

                    // TODO: Validate redirectUrl is in list of approved if toolbar
                    const res = await api.get<AuthenticationFlowResponse>(
                        '/api/client_authorization?' +
                            toParams({
                                code,
                            })
                    )

                    return {
                        name: clientId === 'toolbar' ? 'PostHog Toolbar' : clientId,
                        code,
                        verification: res.verification,
                        redirect_url: redirectUrl,
                    }
                },

                confirmAndRedirect: async () => {
                    if (!values.authentication) {
                        return null
                    }
                    const { redirect_url, verification, code } = values.authentication

                    // TODO: Validate redirectUrl is in list of approved if toolbar

                    await api.create('/api/client_authorization/confirm', {
                        code,
                        verification,
                    })

                    if (redirect_url) {
                        window.location.href = redirect_url
                    }

                    return values.authentication
                },
            },
        ],
    })),

    selectors({
        domain: [
            (s) => [s.authentication],
            (authentication): string | null => {
                return authentication?.redirect_url ? new URL(authentication.redirect_url).host : null
            },
        ],
    }),

    afterMount(({ actions }) => {
        actions.loadAuthenticationFlow()
    }),
])
