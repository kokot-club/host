var Home = Home || {}
var Dashboard = Dashboard || {}
var ErrorPage = ErrorPage || {}

function isLoggedIn() {
    return document.cookie.split('; ').find(row => row.startsWith('auth='))
}

m.route(document.body, '/', {
    '/': {
        view() {
            return !isLoggedIn() ? m.route.set('/login') : m(Dashboard)
        }
    },
    '/login': {
        view() {
            return isLoggedIn() ? m.route.set('/') : m(Login)
        }
    },
    '/error': {
        view() {
            return m(ErrorPage)
        }
    }
})

