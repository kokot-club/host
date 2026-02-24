var UsersList = UsersList || {
    data: {'users': []},
    oninit() {
        m.request({
            url: '/api/admin/list_users',
            method: 'GET'
        }).then(data => {
            console.log(data)
            this.data = data
        })
    },
    view(vnode) {
        return m('table', [
            m('thead', [
                m('tr', [
                    m('th', 'UID'),
                    m('th', 'Username'),
                    m('th', 'Join date'),
                    m('th', 'Role'),
                    m('th', 'Actions')
                ])
            ]),
            m('tbody', this.data.users.map(user => m('tr', [
                m('td', user.id),
                m('td', user.username),
                m('td', user.join_date),
                m('td', user.role),
                m('td', vnode.attrs.callback.map(ctx => {
                    return m('button', {
                        onclick: () => ctx.fn(user.id)
                    }, ctx.label)
                }))
            ])))
        ])
    }
}

var Admin = Admin || {
    fileId: '',
    userId: null,
    view() {
        return m('.settings', [
            m('hgroup', [
                m('h1', 'Admin panel'),
                m('p', 'Various moderation and maintance tools'),
            ]),

            m('hgroup', [
                m('h1', 'Invite system'),
                m('p', 'Invite new users, Purge invites'),
            ]),
            m('.buttons', [
                m('button', {
                    onclick: () => {
                        m.request({
                            url: '/api/admin/generate_invite',
                            method: 'POST'
                        }).then(data => {
                            alert(data.invite)
                        })
                    }
                }, 'Create'),
                m('button.red.secondary', {
                    onclick: () => {
                        m.request({
                            url: '/api/admin/purge_invites',
                            method: 'POST'
                        }).then(data => {
                            alert(data.msg)
                        })
                    }
                }, 'Purge all unused'),
            ]),

            m('hgroup', [
                m('h1', 'User managment'),
                m('p', 'Ban users, Promote users'),
            ]),
            m('.grid', [
                m('h3.setting__title', 'Subject UID'),
                m('input', {
                    value: this.userId,
                    onchange: e => this.userId = e.target.value
                }),
            ]),
            m(UsersList, {
                callback: [{ label: 'Select', fn: id => this.userId = id }]
            }),
            m('.buttons', [
                m('button.red', {
                    onclick: () => {
                        m.request({
                            url: '/api/admin/ban_user',
                            method: 'PATCH',
                            body: {
                                'uid': this.userId,
                                'purge_uploads': true
                            }
                        }).then(data => {
                            alert('Successfuly banned user')
                        })
                    }
                }, 'Ban and purge uploads')
            ]),

            m('hgroup', [
                m('h1', 'Files'),
                m('p', 'Remove files'),
            ]),
            m('.grid', [
                m('h3.setting__title', 'Subject upload ID'),
                m('input', {
                    value: this.fileId,
                    onchange: e => this.fileId = e.target.value
                }),
            ]),
            m('.buttons', [
                m('button.red', {
                    onclick: () => {
                        m.request({url: `/files/delete?uri=${this.fileId}`, method: 'DELETE'}).then(data => {
                            alert('Successfuly removed')
                        })
                    }
                }, 'Remove')
            ]),
        ])
    }
}