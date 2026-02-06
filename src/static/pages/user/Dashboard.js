var Modal = Modal || {}
var Admin = Admin || {}
var Home = Home || {}
var Uploader = Uploader || {}
var Settings = Settings || {}
var Integrations = Integrations || {}
var Files = Files || {}

const isMobile = window.matchMedia('(max-width: 768px)').matches
var sidebarOpen = !isMobile
var dashboardTab = localStorage.getItem('tab') || 'home'

var DashboardTab = DashboardTab || {
    view(vnode) {
        if (dashboardTab == vnode.attrs.tab) {
            document.title = `kokot host - ${vnode.attrs.label}`
        }

        return m('li.sidebar__button', {
            class: dashboardTab == vnode.attrs.tab ? 'sidebar__button--active' : '',
            onclick: vnode.attrs.tab ? () => {
                dashboardTab = vnode.attrs.tab
                localStorage.setItem('tab', vnode.attrs.tab)
                Modal.closeAll()
            } : null,
            ...vnode.attrs
        }, [
            m('.material-symbols-rounded', vnode.attrs.icon),
            m('span', vnode.attrs.label)
        ])
    }
}

var Dashboard = Dashboard || {
    username: 'unknown',
    isAdmin: false,
    storageJob: null,
    storageUsageGb: 0,
    storageCapacityGb: 1,
    updateStorageData() {
        m.request({url: '/files/summary'}).then(data => {
            Dashboard.storageUsageGb = parseFloat(data.usage_mb / 1000).toFixed(2)
            Dashboard.storageCapacityGb = parseFloat(data.storage_mb / 1000).toFixed(2)
        })
    },
    oninit() {
        document.body.addEventListener('dragenter', e => {
            e.preventDefault()
            if (e.dataTransfer.types.includes('Files')) {
                dashboardTab = 'upload'
                m.redraw()
                window.scrollTo(0, 0)
            }
        })
        Dashboard.updateStorageData()

        m.request({url: '/api/user/me'}).then(data => {
            Dashboard.username = data.username
            Dashboard.isAdmin = data.role > 0
        })
    },
    view() {
        return [
            m(Modal),
            m('main.dashboard', [
                m('aside.dashboard__sidebar', {
                    class: !sidebarOpen ? 'dashboard__sidebar--collapsed' : ''
                }, [
                    m('ul.sidebar__nav', [
                        m('hgroup.sidebar__head', [
                            m('p', t('Hello'), ','),
                            m('h1', `${Dashboard.username}!`)
                        ]),
                        m('#mobileMenu', [
                            m(DashboardTab, {
                                label: t('Close'),
                                icon: 'close',
                                onclick: () => {sidebarOpen = false}
                            }),
                            m('hr')
                        ]),
                        m(DashboardTab, {
                            label: t('Home'),
                            icon: 'home',
                            tab: 'home'
                        }),
                        m(DashboardTab, {
                            label: t('Uploader'),
                            icon: 'upload',
                            tab: 'upload'
                        }),
                        m(DashboardTab, {
                            label: t('Integrations'),
                            icon: 'apps',
                            tab: 'integrations'
                        }),
                        m('li', [
                            m('hr')
                        ]),
                        m(DashboardTab, {
                            label: t('My files'),
                            icon: 'folder',
                            tab: 'files'
                        }),
                        this.isAdmin ? [
                            m('li', [
                                m('hr')
                            ]),
                            m(DashboardTab, {
                                label: t('Admin panel'),
                                icon: 'manage_accounts',
                                tab: 'admin'
                            })
                        ] : null,
                    ]),
                    m('ul.sidebar__nav', [
                        m('li', [
                            m('.storage', {title: t('My usage')}, [
                                m('.storage__head', [
                                    m('p.storage__value', `${Dashboard.storageUsageGb}GB`),
                                    m('p.storage__value', `${Dashboard.storageCapacityGb}GB`),
                                ]),
                                m('progress.storage__progress', {
                                    min: 0,
                                    max: 1,
                                    value: Dashboard.storageUsageGb/Dashboard.storageCapacityGb
                                })
                            ]),
                        ]),
                        m(DashboardTab, {
                            label: t('Settings'),
                            icon: 'settings',
                            tab: 'settings'
                        }),
                        m('li.sidebar__item', [
                            m('a', { href: '/api/user/logout' }, [
                                m('.sidebar__button', [
                                    m('.material-symbols-rounded', 'logout'),
                                    m('span', t('Log out'))
                                ]),
                            ])
                        ])
                    ])
                ]),
                m('div.dashboard__root', [
                    m('nav.dashboard__navbar', [
                        m('ul.navbar__content', [
                            m('li.navbar__button', {
                                title: t('Toggle sidebar'),
                                onclick: e => {sidebarOpen = !sidebarOpen}
                            }, [
                                m('.material-symbols-rounded', 'side_navigation')
                            ])
                        ]),
                        m('ul.navbar__content', [

                        ])
                    ]),
                    m('section.dashboard__content', {
                        onclick: e => {
                            if (isMobile) {
                                sidebarOpen = false
                            }
                        }
                    }, [
                        (() => {
                            switch (dashboardTab) {
                                case 'admin': return m(Admin)
                                case 'home': return m(Home)
                                case 'upload': return m(Uploader)
                                case 'settings': return m(Settings)
                                case 'integrations': return m(Integrations)
                                case 'files': return m(Files)
                            }
                        })()
                    ])
                ])
            ])
        ]
    }
}