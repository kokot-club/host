var Theme = Theme || {
    view() {
        return m('select', {
            value: localStorage.getItem('theme') || 'light',
            onchange: e => {
                const next = e.target.value
                root.dataset.theme = next
                localStorage.setItem('theme', next)
            }
        }, [
            m('option', {value: 'light'}, t('Light')),
            m('option', {value: 'dark'}, t('Dark'))
        ])
    }
}