from posthog.cdp.templates.hog_function_template import HogFunctionTemplate


template: HogFunctionTemplate = HogFunctionTemplate(
    status="alpha",
    id="template-rudderstack",
    name="Send data to RudderStack",
    description="Send data to RudderStack",
    icon_url="/api/projects/@current/hog_functions/icon/?id=rudderstack.com",
    hog="""
let host := inputs.host
let token := inputs.token
let propertyOverrides := inputs.properties
let properties := include_all_properties ? event.properties : {}

for (let key, value in propertyOverrides) {
    properties[key] := value
}

let rudderPayload := {
    'context': {
        'app': {
            'name': 'PostHogPlugin',
        }
        'os': {
            'name': event.properties.$os
        },
        'browser': event.properties.$browser,
        'browser_version': event.properties.$browser_version,
        'page': {
            'host': event.properties.$host,
            'url': event.properties.$current_url,
            'path': event.properties.$pathname,
            'referrer': event.properties.$referrer,
            'initial_referrer': event.properties.$initial_referrer,
            'referring_domain': event.properties.$referring_domain,
            'initial_referring_domain': event.properties.$initial_referring_domain,
        },
        'screen': {
            'height': event.properties.$screen_height,
            'width': event.properties.$screen_width,
        },
        'library': {
            'name': event.properties.$lib,
            'version': event.properties.$lib_version,
        },
        'ip': event.ip, // TODO: Add IP
        'active_feature_flags': event.properties.$active_feature_flags,
        'posthog_version': event.properties.posthog_version,
        'token': event.properties.token
    }
    'channel': 's2s',
    'messageId': event.uuid,
    'originalTimestamp': event.timestamp,
    'userId': event.properties.$user_id ?? event.distinct_id,
    'anonymousId': event.properties.$anon_distinct_id ?? event.properties.$device_id ?? event.properties.distinct_id,
    'type': 'track',
    'properties': {},
}

if (event.name === '$pageview') {
    rudderPayload.type = 'page'
    rudderPayload.name = event.properties.name

    rudderPayload.properties.category = event.properties.category
    rudderPayload.properties.host = event.properties.$host
    rudderPayload.properties.url = event.properties.$current_url
    rudderPayload.properties.path = event.properties.$pathname
    rudderPayload.properties.referrer = event.properties.$referrer
    rudderPayload.properties.initial_referrer = event.properties.$initial_referrer
    rudderPayload.properties.referring_domain = event.properties.$referring_domain
    rudderPayload.properties.initial_referring_domain = event.properties.$initial_referring_domain
}


// add generic props
constructPayload(rudderPayload, event, generic)

// get specific event props
const eventName = get(event, 'event')
const { type, mapping } = eventToMapping[eventName] ? eventToMapping[eventName] : eventToMapping['default']

//set Rudder payload type
set(rudderPayload, 'type', type)

// set Rudder event props
constructPayload(rudderPayload, event, mapping)

// add all pther posthog keys under props not starting with $ to Rudder payload properties
Object.keys(event.properties).forEach((propKey) => {
    if (propKey.slice(0, 1) != '$' && event.properties[propKey] != undefined && event.properties[propKey] != null) {
        set(rudderPayload, `properties.${propKey}`, event.properties[propKey])
    }
})

return rudderPayload


let payload := {
    'batch': [batchItem],
    'sentAt': now()
}

fetch(f'{host}/v1/batch', {
    'method': 'POST',
    'headers': {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {base64Encode(f'{inputs.token}:')}',
    },
    'body': payload
})
""".strip(),
    inputs_schema=[
        {
            "key": "host",
            "type": "string",
            "label": "Rudderstack host",
            "description": "The destination of the Rudderstack instance",
            "default": "https://hosted.rudderlabs.com",
            "secret": False,
            "required": True,
        },
        {
            "key": "token",
            "type": "string",
            "label": "Write API key",
            "description": "RudderStack Source Writekey",
            "secret": False,
            "required": True,
        },
    ],
)
