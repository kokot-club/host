var PasswordInput = PasswordInput || {
    password: '',
    view(vnode) {
        return m('label.form__input', t(vnode.attrs.title || 'Password'), [
            m('input', {
                oninput: e => {
                    this.password = e.target.value
                    vnode.attrs.callback(e)
                },
                type: 'password',
                placeholder: t(vnode.attrs.hint || 'Min. 8 characters'),
                autocomplete: 'password'
            }),
            (() => {
                const strength = this.password.length < 8 ? 0 : this.password.length / 32;
                const thresholds = [0.25, 0.5, 0.75, 1];
                const colors = thresholds.map(t => strength >= t ? 'green' : 'crust');
                
                function getMessage() {
                    if (strength < 0.25) return 'Add more characters';
                    if (strength < 0.5) return 'Your password could be stronger';
                    if (strength < 0.75) return 'Your password is good';
                    return 'Your password is great!';
                };
                
                return [
                    m('.input__password-strength', colors.map(color => m('.strength-indicator', {style: {backgroundColor: `var(--${color})`}}))),
                    m('small', t(getMessage()))
                ]
            })()
        ])
    }
}