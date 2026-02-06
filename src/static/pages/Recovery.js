var PasswordInput = PasswordInput || {}

var Recovery = Recovery || {
    busy: false,
    password: '',
    password_secondary: '',
    errorMsg: '',
    successMsg: '',
    oninit() {
        setTimeout(() => {
            const s = document.createElement('script')
            s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js'
            s.async = true
            s.defer = true
            document.head.appendChild(s) 
        }, 500)
    },
    onsubmit(e) {
        e.preventDefault()
        this.busy = true

        var challengeToken = ''
        const challengeField = document.querySelector('[name="cf-turnstile-response"]')
        if (challengeField) {
            challengeToken = challengeField.value
        }

        const formData = new FormData()
        formData.append('password', this.password)
        formData.append('password_secondary', this.password_secondary)
        formData.append('recovery_code', new URLSearchParams(window.location.hash.split('?')[1]).get('recovery_code'))
        formData.append('challenge', challengeToken)

        m.request({
            method: 'POST',
            url: '/api/user/recovery',
            body: formData
        })
        .then(data => {
            this.successMsg = data.msg
            this.errorMsg = null
            // this.busy = false
        })
        .catch(err => {
            this.errorMsg = err.response.error
            this.busy = false
        }).finally(() => {
            turnstile.reset('.cf-turnstile')
        })
    },
    view() {
        localStorage.removeItem('tab')
        document.title = t('Password recovery')

        return m('main.login__container', [
            m('article', {
                style: 'max-width: 420px; margin-inline: 1rem'
            }, [
                m('hgroup.login__header', [
                    m('h1.login__title', t('You are now changing your password')),
                ]),
                this.errorMsg || this.successMsg ? m('.alert.login__alert', {
                    class: this.errorMsg ? 'alert--error' : 'alert--success'
                }, t(this.errorMsg) || [
                    t(this.successMsg),
                    m('a.link', {
                        href: '/'
                    }, t('Go back'))
                ]) : null,
                m('form', {onsubmit: e => this.onsubmit(e)}, [
                    m('fieldset', [
                        m(PasswordInput, {
                            title: 'New password',
                            callback: e => {this.password = e.target.value}
                        }),
                        m('.form__control', [
                            m('label.form__input', t('Confirm your password'), [
                                m('input', {
                                    oninput: (e) => {this.password_secondary = e.target.value},
                                    type: 'password',
                                    autocomplete: 'password'
                                })
                            ]),
                        ]),
                        typeof(CLOUDFLARE_TURNSTILE_SITE) != 'undefined' ? m('.form__input', 'Captcha', [
                            m('.cf-turnstile', {
                                'data-sitekey': CLOUDFLARE_TURNSTILE_SITE,
                                'data-size': 'flexible',
                                'data-theme': 'light'
                            }),
                        ]) : null,
                    ]),
                    m('.buttons.grid', [
                        m('button[type="submit"]', {
                            disabled: this.busy ? 'true' : '',
                        }, t('Change'))
                    ])
                ])
            ])
        ])
    }
}