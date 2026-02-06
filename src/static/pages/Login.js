var PasswordInput = PasswordInput || {}

var PasswordRecoveryModal = PasswordRecoveryModal || {
    user: '',
    busy: false,
    opened: false,
    errorMsg: '',
    successMsg: '',
    openModal() {
        this.opened = true
        turnstile.reset('.cf-turnstile#turnstile--recovery')
    },
    onsubmit(e) {
        e.preventDefault()
        this.busy = true

        var challengeToken = ''
        const challengeField = document.querySelector('#turnstile--recovery [name="cf-turnstile-response"]')
        if (challengeField) {
            challengeToken = challengeField.value
        }

        const formData = new FormData()
        formData.append('user', this.user)
        formData.append('challenge', challengeToken)

        m.request({
            method: 'POST',
            url: '/api/user/trigger_recovery',
            body: formData
        })
        .then(data => {
            this.successMsg = data.msg
            this.errorMsg = null
            this.busy = false
        })
        .catch(err => {
            this.errorMsg = err.response.error
            this.busy = false
        }).finally(() => {
            turnstile.reset('.cf-turnstile#turnstile--recovery')
        })
    },
    view() {
        return m('.dialog', {
            style: `display: ${this.opened ? 'inherit' : 'none'}`
        }, [
            m('.dialog__body', {
                style: 'width: 500px'
            }, [
                m('.dialog__nav', [
                    m('.dialog__title', t('Password recovery')),
                ]),
                m('.alert', [
                    t('Important: You must link your Discord account and allow DMs from our server to receive the recovery link')
                ]),
                m('form', {onsubmit: e => this.onsubmit(e)}, [
                    m('fieldset', [
                        m('.form__control', [
                            m('label.form__input', t('Username'), [
                                m('input', {
                                    oninput: (e) => {this.user = e.target.value},
                                    autocomplete: 'username'
                                })
                            ]),
                        ]),
                        typeof(CLOUDFLARE_TURNSTILE_SITE) != 'undefined' ? m('.form__input', 'Captcha', [
                            m('.cf-turnstile#turnstile--recovery', {
                                'data-sitekey': CLOUDFLARE_TURNSTILE_SITE,
                                'data-size': 'flexible',
                                'data-theme': 'light'
                            }),
                        ]) : null,
                    ]),
                    m('.buttons.grid', [
                        m('button[type="submit"]', {
                            disabled: this.busy
                        }, t('Send')),
                        m('button.white', {
                            disabled: this.busy,
                            onclick: e => {e.preventDefault(); PasswordRecoveryModal.opened = false}
                        }, t('Cancel'))
                    ])
                ]),
                this.errorMsg || this.successMsg ? m('.alert.login__alert', {
                    class: this.errorMsg ? 'alert--error' : 'alert--success'
                }, t(this.errorMsg) || t(this.successMsg)) : null,
            ])
        ])
    }
}

var Login = Login || {
    user: '',
    password: '',
    invite: '',
    isLogin: true,
    busy: false,
    errorMsg: null,
    successMsg: null,
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
        const challengeField = document.querySelector('#turnstile--login [name="cf-turnstile-response"]')
        if (challengeField) {
            challengeToken = challengeField.value
        }

        const formData = new FormData()
        formData.append('user', this.user)
        formData.append('password', this.password)
        formData.append('invite', this.invite)
        formData.append('challenge', challengeToken)

        m.request({
            method: 'POST',
            url: `/api/user/${this.isLogin ? 'login' : 'register'}`,
            body: formData
        })
        .then(data => {
            if (data['did_login'] == true) {
                window.location.reload()
                return
            }

            this.successMsg = data.msg
            this.errorMsg = null
            this.isLogin = true
            this.busy = false
        })
        .catch(err => {
            this.errorMsg = err.response.error
            this.busy = false
        }).finally(() => {
            turnstile.reset('.cf-turnstile#turnstile--login')
        })
    },
    view() {
        localStorage.removeItem('tab')
        document.title = 'Log in'

        return m('main.login__container', [
            m(PasswordRecoveryModal),
            m('article.login', [
                m('hgroup.login__header', [
                    m('h1.login__title', t('Log in')),
                    m('span', this.isLogin ? t('Welcome back!') : t("Let's make an account"))
                ]),
                this.errorMsg || this.successMsg ? m('.alert.login__alert', {
                    class: this.errorMsg ? 'alert--error' : 'alert--success'
                }, t(this.errorMsg) || t(this.successMsg)) : null,
                m('form', {onsubmit: e => this.onsubmit(e)}, [
                    m('fieldset', [
                        m('.form__control', [
                            m('label.form__input', t('Username'), [
                                m('input', {
                                    oninput: (e) => {this.user = e.target.value},
                                    placeholder: t('No special characters'),
                                    autocomplete: 'username'
                                })
                            ]),
                        ]),
                        m('.form__control', [
                            m('label.form__input', t('Password'), [
                                !this.isLogin ? m(PasswordInput, {
                                    callback: e => {this.password = e.target.value}
                                }) : [
                                    m('input', {
                                        oninput: (e) => {this.password = e.target.value},
                                        type: 'password',
                                        placeholder: t('Min. 8 characters'),
                                        autocomplete: 'password'
                                    }),
                                    m('small.link', {
                                        onclick: e => {PasswordRecoveryModal.openModal()}
                                    }, t('Forgot your password?'))
                                ]
                            ]),
                        ]),
                        !this.isLogin ? [
                            m('.form__control', [
                                m('label.form__input', t('Invite'), [
                                    m('input', {
                                        oninput: e => {this.invite = e.target.value},
                                        autocomplete: 'false'
                                    })
                                ]),
                            ])
                        ] : null,
                        typeof(CLOUDFLARE_TURNSTILE_SITE) != 'undefined' ? m('.form__input', 'Captcha', [
                            m('.cf-turnstile#turnstile--login', {
                                'data-sitekey': CLOUDFLARE_TURNSTILE_SITE,
                                'data-size': 'flexible',
                                'data-theme': 'light'
                            }),
                        ]) : null,
                    ]),
                    m('.buttons.grid', [
                        m('button[type="submit"]', {
                            disabled: this.busy ? 'true' : '',
                        }, this.isLogin ? t('Log in') : t('Register'))
                    ]),
                    m('p', [
                        m('span', typeof(SUPPORT_HANDLE) != 'undefined' ? `${t('Help')}: @${SUPPORT_HANDLE} • ` : ''),
                        m('a.link', {onclick: () => {
                            this.isLogin = !this.isLogin
                        }}, this.isLogin ? t('Looking to register?') : t('Log in'))
                    ])
                ])
            ])
        ])
    }
}