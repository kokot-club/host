var Login = Login || {}
var Recovery = Recovery || {}
var ErrorPage = ErrorPage || {}
var Home = Home || {}
var Dashboard = Dashboard || {}

const isLoggedIn = document.cookie.split('; ').find(row => row.startsWith('auth='))
const hasRecoveryCode = new URLSearchParams(window.location.hash.split('?')[1]).get('recovery_code') != null

m.route(document.body, '/', {
    '/': {
        view() {
            return !isLoggedIn ? m.route.set('/login') : m(Dashboard)
        }
    },
    '/login': {
        view() {
            return isLoggedIn ? m.route.set('/') : m(Login)
        }
    },
    '/recovery': {
        view() {
            return (isLoggedIn || hasRecoveryCode) ? m(Recovery) : m.route.set('/')
        }
    },
    '/error': {
        view() {
            return m(ErrorPage)
        }
    }
})
