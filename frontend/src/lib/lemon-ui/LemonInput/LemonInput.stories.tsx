import { useState } from 'react'
import { Meta, StoryFn, StoryObj } from '@storybook/react'

import { LemonInput } from './LemonInput'
import { IconArrowDropDown, IconCalendar } from 'lib/lemon-ui/icons'
import { LemonButtonWithDropdown } from 'lib/lemon-ui/LemonButton'

type Story = StoryObj<typeof LemonInput>
const meta: Meta<typeof LemonInput> = {
    title: 'Lemon UI/Lemon Input',
    component: LemonInput,
    tags: ['autodocs'],
    args: {
        value: 'Foo',
    },
}
export default meta

const Template: StoryFn<typeof LemonInput> = (props) => {
    const [value, setValue] = useState(props.value)
    // @ts-expect-error – union variant inference around the `type` prop doesn't work here as `type` comes from above
    return <LemonInput {...props} value={value} onChange={(newValue) => setValue(newValue)} />
}

export const Basic: Story = {
    render: Template,
}

export const WithPrefixAndSuffixAction: Story = {
    render: Template,

    args: {
        prefix: <IconCalendar />,
        suffix: (
            <LemonButtonWithDropdown
                noPadding
                dropdown={{
                    overlay: 'Surprise! 😱',
                }}
                type="tertiary"
                icon={<IconArrowDropDown />}
            />
        ),
    },
}

export const Search: Story = {
    render: Template,
    args: { type: 'search', placeholder: 'Search your soul' },
}

export const Password: Story = {
    render: Template,
    args: { type: 'password', placeholder: 'Enter your password' },
}

export const Disabled: Story = {
    render: Template,
    args: { disabled: true },
}

export const DangerStatus: Story = {
    render: Template,
    args: { status: 'danger' },
}

export const Clearable: Story = {
    render: Template,
    args: { allowClear: true },
}

export const Numeric: Story = {
    render: Template,
    args: { type: 'number', min: 0, step: 1, value: 3 },
}

export const Small: Story = {
    render: Template,
    args: { allowClear: true, size: 'small' },
}
