var Recovery = Recovery || {
    busy: false,
    password: '',
    passwordSecondary: '',
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
        formData.append('password_secondary', this.passwordSecondary)
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
                        m('.form__control', [
                            m('label.form__input', t('New password'), [
                                m('input', {
                                    oninput: (e) => {this.password = e.target.value},
                                    type: 'password',
                                    placeholder: t('Min. 8 characters'),
                                    autocomplete: 'password'
                                }),
                                
                                (() => {
                                    const strength = this.password.length / 32;
                                    const thresholds = [0.25, 0.5, 0.75, 1];
                                    const colors = thresholds.map(t => strength >= t ? 'green' : 'crust');
                                    
                                    const getMessage = () => {
                                        if (strength < 0.25) return 'Add more characters';
                                        if (strength < 0.5) return 'Your password could be stronger';
                                        if (strength < 0.75) return 'Your password is good';
                                        return 'Your password is great!';
                                    };
                                    
                                    return [
                                        m('.input__password-strength', colors.map(color => m('.strength-indicator', {style: {backgroundColor: `var(--${color})`}}))),
                                        m('small', t(getMessage()))
                                    ];
                                })()
                            ]),
                        ]),
                        m('.form__control', [
                            m('label.form__input', t('Confirm your password'), [
                                m('input', {
                                    oninput: (e) => {this.passwordSecondary = e.target.value},
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