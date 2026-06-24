var Login = Login || {}
var Recovery = Recovery || {}
var ErrorPage = ErrorPage || {}
var Home = Home || {}
var Dashboard = Dashboard || {}

const hasRecoveryCode = new URLSearchParams(window.location.hash.split('?')[1]).get('recovery_code') != null

m.route(document.body, '/', {
    '/': {
        view() {
            return !IS_AUTHENTICATED ? m.route.set('/login') : m(Dashboard)
        }
    },
    '/login': {
        view() {
            return IS_AUTHENTICATED ? m.route.set('/') : m(Login)
        }
    },
    '/recovery': {
        view() {
            return (IS_AUTHENTICATED || hasRecoveryCode) ? m(Recovery) : m.route.set('/')
        }
    },
    '/error': {
        view() {
            return m(ErrorPage)
        }
    }
})
