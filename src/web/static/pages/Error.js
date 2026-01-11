var ErrorPage = ErrorPage || {
    view() {
        return m('main.center', [
            m('article.web-error', [
                m('img', {width: '100%', src: '/static/images/kokot.png', alt: 'kokot.club logo'}),
                m('h1', 'Something went wrong...'),
                m('small', 'Go back to ', [
                    m('a.link', {href: '/'}, 'the dashboard')
                ])
            ])
        ])
    }
}