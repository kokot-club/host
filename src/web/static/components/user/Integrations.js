var Integrations = Integrations || {
    didReset: false,
    view() {
        return m('.settings', [
            m('hgroup', [
                m('h1', t('Upload key')),
                m('p', t('This key allows external programs to interact with our service')),
            ]),
            m('.alert', [
                m('p', {style: 'margin-top: 0'}, t('Resetting your key will invalidate all installed configurations, you will have to set-up your integrations again')),
                m('.buttons', [
                    m('button.red', {
                        onclick: e => {
                            if (this.didReset) {
                                return
                            }

                            m.request({url: '/files/regenerate_upload_key', method: 'POST'}).then(data => {
                                this.didReset = true
                            })
                        }
                    }, this.didReset ? t('Success!') : t('Reset my key')),
                ]),
            ]),
            m('hgroup', [
                m('h1', t('Supported integrations'))
            ]),
            m('.grid', [
                m('.card', [
                    m('img', {
                        src: '/static/images/sharex.png',
                        alt: 'ShareX logo'
                    }),
                    m('h1', 'ShareX'),
                    m('.buttons', [
                        m('a', {
                            href: '/files/integration?integration_type=sharex'
                        }, [
                            m('button', t('Download configuration'))
                        ]),
                        m('a', {
                            href: 'https://getsharex.com/',
                            target: '_blank',
                            rel: 'noopener noreferrer'
                        }, [
                            m('button.secondary', t('Get'), ' ShareX', [
                                m('.material-symbols-rounded', 'open_in_new')
                            ])
                        ]),
                    ]),
                ])
            ])
        ])
    }
}