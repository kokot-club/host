var Theme = Theme || {}
var Language = Language || {}

var DynamicStringsPopup = DynamicStringsPopup || {
    opened: false,
    view() {
        if (!this.opened) {
            return
        }

        return m('.dialog', [
            m('.dialog__body', {
                style: 'width: 300px'
            }, [
                m('.dialog__nav', [
                    m('h1.dialog__title', t('Available strings')),
                ]),
                m('ul', [
                    m('li', [
                        m('hgroup', [
                            m('h3', '%date%'),
                            m('p', t('Date when the file was uploaded'))
                        ])
                    ]),
                    m('li', [
                        m('hgroup', [
                            m('h3', '%size%'),
                            m('p', t('Total file size represented in megabytes (MB)'))
                        ])
                    ]),
                    m('li', [
                        m('hgroup', [
                            m('h3', '%filename%'),
                            m('p', t('Original file name of the upload'))
                        ])
                    ]),
                    m('li', [
                        m('hgroup', [
                            m('h3', '%owner%'),
                            m('p', t('The user that uploaded the file'))
                        ])
                    ])
                ]),
                m('.buttons.pills', [
                    m('button', {
                        onclick: e => {DynamicStringsPopup.opened = false}
                    }, t('Cancel'))
                ])
            ])
        ])
    }
}

var Settings = Settings || {
    // meta
    busy: false,
    msg: '',
    errorMsg: '',

    // account linking
    discordUsername: null,
    discordHeadshot: null,
    discordUnlinkConfirm: false,

    // settings
    embed_title: '',
    embed_sitename: '',
    embed_siteurl: '',
    embed_authorname: '',
    embed_authorurl: '',
    embed_description: '',
    embed_color: '#9ca0b0',
    anonymous: false,
    auto_expire: 0,

    oncreate() {
        m.request({
            method: 'GET',
            url: '/api/user/discord'
        })
        .then(response => {
            this.discordUsername = response.username || this.discordUsername
            this.discordHeadshot = response.headshot || this.discordHeadshot
            m.redraw()
        })
        .catch(error => {

        })

        m.request({
            method: 'GET',
            url: '/api/user/settings'
        })
        .then(response => {
            this.embed_title = response.embed_title || this.embed_title
            this.embed_sitename = response.embed_sitename || this.embed_sitename
            this.embed_siteurl = response.embed_siteurl || this.embed_siteurl
            this.embed_authorname = response.embed_authorname || this.embed_authorname
            this.embed_authorurl = response.embed_authorurl || this.embed_authorurl
            this.embed_description = response.embed_description || this.embed_description
            this.embed_color = response.embed_color || this.embed_color
            this.anonymous = response.anonymous || this.anonymous
            this.auto_expire = response.auto_expire || this.auto_expire
            m.redraw()
        })
        .catch(error => {

        })
    },
    onsubmit(e) {
        e.preventDefault()
        if (this.busy) {
            return
        }
        
        this.busy = true
        const formData = new FormData()
        formData.append('embed_title', this.embed_title)
        formData.append('embed_sitename', this.embed_sitename)
        formData.append('embed_siteurl', this.embed_siteurl)
        formData.append('embed_authorname', this.embed_authorname)
        formData.append('embed_authorurl', this.embed_authorurl)
        formData.append('embed_description', this.embed_description)
        formData.append('embed_color', this.embed_color)
        formData.append('anonymous', this.anonymous)
        formData.append('auto_expire', this.auto_expire)

        m.request({
            method: 'POST',
            url: '/api/user/settings',
            body: formData
        })
        .then(() => {
            this.busy = false
            m.redraw()
        })
        .catch(error => {
            this.busy = false
            m.redraw()
        })
    },

    view() {
        return m('.settings', [
            m(DynamicStringsPopup),
            m('hgroup', [
                m('h1', t('Website settings')),
                m('p', t('Theming and user experience')),
            ]),
            m('.grid', [
                m('hgroup.settings__text', [
                    m('h3', t('Site theme')),
                    m('p', t('Stored locally'))
                ]),
                m(Theme)
            ]),
            m('.grid', [
                m('hgroup.settings__text', [
                    m('h3', t('Site language')),
                    m('p', t('Stored locally'))
                ]),
                m(Language)
            ]),

            m('hgroup', [
                m('h1', t('Account settings')),
                m('p', t('Further secure your account')),
            ]),
            m('div', [
                m('hgroup.settings__text', [
                    m('h3', t('Account info')),
                    m('p', t('Change your Username or Password'))
                ]),
                m('.buttons', [
                    m('a', {
                        href: '/#!/recovery',
                        target: '_blank',
                        rel: 'noopener noreferrer'
                    }, [
                        m('button.red', t('Change Password'), [
                            m('.material-symbols-rounded', 'open_in_new')
                        ])
                    ])
                ])
            ]),
            m('.alert', (() => {
                    if (this.discordUsername) {
                        return [
                            m('hgroup', [
                                m('h2', t('Thank you for linking your Discord account!')),
                            ]),
                            m('.profile-card', [
                                m('img.profile-card__headshot', {
                                    src: this.discordHeadshot
                                }),
                                m('h1', this.discordUsername)
                            ]),
                            m('.buttons', [
                                m('button.green.secondary', {
                                    disabled: true
                                }, [
                                    m('.material-symbols-rounded', 'check')
                                ], t('Linked!')),
                                m('button.red', {
                                    onclick: e => {
                                        if (this.discordUnlinkConfirm) {
                                            m.request({
                                                method: 'DELETE',
                                                url: '/api/user/unlink_discord'
                                            })
                                            .then(response => {
                                                location.reload()
                                            })
                                            .catch(error => {

                                            })
                                        }

                                        this.discordUnlinkConfirm = true
                                    }
                                }, this.discordUnlinkConfirm ? t('Are you sure?') : t('Unlink'))
                            ])
                        ]
                    }
                    
                    return [
                        m('hgroup', [
                            m('h2', t('Link your Discord account!')),
                            m('p', t('You will receive account alerts and password reset requests straight to your direct messages'))
                        ]),
                        m('.buttons', [
                            m('a', {
                                href: '/api/user/link_discord'
                            }, [
                                m('button.green', [
                                    m('.material-symbols-rounded', 'link_2')
                                ], t('Link now'))
                            ])
                        ])
                    ]
                })()),
            m('.grid', [
                m('hgroup.settings__text', [
                    m('h3', t('Anonymous mode')),
                    m('p', t('Your name will not be displayed anywhere on the site'))
                ]),
                m('select', {
                    value: String(Boolean(this.anonymous)),
                    onchange: e => this.anonymous = e.target.value == 'true'
                }, [
                    m('option', {value: 'true'}, t('Yes')),
                    m('option', {value: 'false'}, t('No'))
                ])
            ]),

            m('hgroup', [
                m('h1', t('Embed Settings')),
                m('p', t('Customize how social media platforms should render rich content of your uploads')),
                m('p', t('Check out our dynamic strings list for more expressive embeds, these strings can be placed everywhere in all fields'))
            ]),
            m('.buttons', [
                m('button', {
                    onclick: e => {DynamicStringsPopup.opened = true}
                }, t('Dynamic strings')),
                m('button.white', {
                    onclick: () => {
                        this.embed_title = ''
                        this.embed_sitename = ''
                        this.embed_siteurl = ''
                        this.embed_authorname = ''
                        this.embed_authorurl = ''
                        this.embed_description = ''
                    }
                }, t('Clear all fields'))
            ]),
            m('.grid', [
                m('hgroup.settings__text', [
                    m('h3', t('Title')),
                ]),
                m('input', {
                    value: this.embed_title,
                    onchange: e => this.embed_title = e.target.value,
                    placeholder: ''
                })
            ]),
            m('.grid', [
                m('hgroup.settings__text', [
                    m('h3', t('Site name')),
                ]),
                m('input', {
                    value: this.embed_sitename,
                    onchange: e => this.embed_sitename = e.target.value,
                    placeholder: ''
                })
            ]),
            m('.grid', [
                m('hgroup.settings__text', [
                    m('h3', t('Site URL')),
                ]),
                m('input', {
                    value: this.embed_siteurl,
                    onchange: e => this.embed_siteurl = e.target.value,
                    placeholder: 'https://'
                })
            ]),
            m('.grid', [
                m('hgroup.settings__text', [
                    m('h3', t('Author name')),
                ]),
                m('input', {
                    value: this.embed_authorname,
                    onchange: e => this.embed_authorname = e.target.value,
                    placeholder: ''
                })
            ]),
            m('.grid', [
                m('hgroup.settings__text', [
                    m('h3', t('Author URL')),
                ]),
                m('input', {
                    value: this.embed_authorurl,
                    onchange: e => this.embed_authorurl = e.target.value,
                    placeholder: 'https://'
                })
            ]),
            m('.grid', [
                m('hgroup.settings__text', [
                    m('h3', t('Description')),
                ]),
                m('input', {
                    value: this.embed_description,
                    onchange: e => this.embed_description = e.target.value,
                    placeholder: ''
                })
            ]),
            m('.grid', [
                m('hgroup.settings__text', [
                    m('h3', t('Embed color')),
                ]),
                m('.grid', [
                    m('input', {
                        style: 'height: 100%; width: 100%',
                        type: 'color',
                        value: this.embed_color,
                        onchange: e => this.embed_color = e.target.value
                    }),
                    m('input', {
                        value: this.embed_color,
                        onchange: e => this.embed_color = e.target.value,
                        placeholder: '#ff0000'
                    })
                ])
            ]),

            m('hgroup', [
                m('h1', t('Upload settings')),
                m('p', t('What happens to your uploads')),
            ]),
            m('.grid', [
                m('hgroup.settings__text', [
                    m('h3', t('Auto expire files')),
                    m('p', t('(This won\'t affect existing uploads) Sets the expiration time for web and integration uploads')),
                ]),
                m('select', {
                    value: this.auto_expire,
                    onchange: e => this.auto_expire = e.target.value
                }, [
                    m('option', {value: 0}, t('Never')),
                    m('option', {value: 3600}, t('1 hour')),
                    m('option', {value: 7200}, t('12 hours')),
                    m('option', {value: 86400}, t('1 day')),
                    m('option', {value: 259200}, t('3 days')),
                ])
            ]),

            m('.buttons.grid', [
                m('button', {
                    onclick: e => this.onsubmit(e),
                    disabled: this.busy
                }, t('Save all'))
            ])
        ])
    }
}

