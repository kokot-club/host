var Integrations = Integrations || {
    didReset: false,
    didCopy: false,
    uploadKey: '',
    oncreate() {
        m.request({
            method: 'GET',
            url: '/files/integration?integration_type=other'
        })
        .then(response => {
            this.uploadKey = response.upload_key
            m.redraw()
        })
        .catch(error => {

        })
    },
    view() {
        return m('.settings', [
            m('hgroup', [
                m('h1', t('Upload key')),
                m('p', t('This key allows external programs to interact with our service')),
            ]),
            m('.alert', [
                m('p', {style: 'margin-top: 0'}, t('Resetting your key will invalidate all installed configurations, you will have to set-up your integrations again')),
                m('input', {
                    style: 'margin-bottom: 1rem',
                    type: 'password',
                    readonly: true,
                    value: this.uploadKey
                }),
                m('.buttons', [
                    m('button', {
                        onclick: e => {
                            navigator.clipboard.writeText(this.uploadKey)
                            this.didCopy = true
                        }
                    }, this.didCopy ? '' : t('Copy'), [
                        m('.material-symbols-rounded', this.didCopy ? 'check' : 'content_copy')
                    ]),
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