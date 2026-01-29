var Language = Language || {
    view() {
        return m('select', {
            value: localStorage.getItem('lang') || getLanguage() || 'en',
            onchange: e => {
                const next = e.target.value
                localStorage.setItem('lang', next)
            }
        }, [
            m('option', {value: 'en'}, '🇺🇸 English (Default)'),
            m('option', {value: 'pl'}, '🇵🇱 Polski'),
            m('option', {value: 'de'}, '🇩🇪 Deutsch'),
            m('option', {value: 'ru'}, '🇷🇺 Русский')
        ])
    }
}