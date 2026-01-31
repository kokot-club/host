var files = []

function deleteFile(uri) {
    files = files.filter(f => f.uri != uri)
    m.request({url: `/files/delete?uri=${uri}`, method: 'DELETE'}).then(data => {
        Dashboard.updateStorageData()
        return true
    })

    return false
}

function renameFile(uri, newFilename) {
    files = files.filter(f => f.uri != uri)
    m.request({url: `/files/edit`, method: 'PUT', body: {uri: uri, new_filename: newFilename}}).then(data => {
        window.location.reload()
        return true
    })

    return false
}

var FileContext = FileContext || {
    didCopy: false,
    confirmDelete: false,
    opened: false,
    data: null,
    ref: null,
    openWith(data, ref) {
        FileContext.didCopy = false
        FileContext.confirmDelete = false
        FileContext.data = data
        FileContext.ref = ref
        FileContext.opened = true
    },
    view() {
        if (!FileContext.opened) {
            return
        }

        return m('.dialog', [
            m('.dialog__body', {
                style: 'width: 300px'
            }, [
                m('.dialog__nav', [
                    m('.dialog__title', t('Menu')),
                ]),
                m('.buttons.pills', [
                    m('button.white', {
                        onclick: e => {
                            navigator.clipboard.writeText(FileContext.data.url)
                            FileContext.didCopy = true
                        }
                    }, FileContext.didCopy ? [
                        m('.material-symbols-rounded', 'check')
                    ] : t('Copy URL')),
                    m('a.pills', {
                        href: FileContext.data.url,
                        target: '_blank',
                        rel: 'noopener noreferrer'
                    }, [
                        m('button.white', t('Open'), [
                            m('.material-symbols-rounded', 'open_in_new')
                        ])
                    ]),
                    m('button.red', {
                        onclick: e => {
                            if (this.confirmDelete) {
                                let didDelete = deleteFile(FileContext.data.uri)
                                FileContext.opened = false
                                return
                            }

                            FileContext.confirmDelete = true
                        }
                    }, FileContext.confirmDelete ? t('Are you sure?') : t('Delete')),
                    m('button.secondary', {
                        onclick: e => {FileContext.opened = false}
                    }, t('Cancel'))
                ])
            ])
        ])
    }
}

var FileRecord = FileRecord || {
    didCopy: false,
    view(vnode) {
        if (this.hidden) {
            return
        }

        const data = vnode.attrs.data
        switch (vnode.attrs.display) {
            case 'grid':
            return m('.file--cell.card', [
                m('.file__actions--cell', [
                    m('.buttons', [
                        m('button.white.secondary.compact', {
                            onclick: e => {
                                navigator.clipboard.writeText(data.url)
                                this.didCopy = true
                            }
                        }, [
                            m('.material-symbols-rounded', this.didCopy ? 'check' : 'content_copy')
                        ]),
                        m('a', {
                            href: data.url,
                            target: '_blank',
                            rel: 'noopener noreferrer'
                        }, [
                            m('button.white.secondary.compact', [
                                m('.material-symbols-rounded', 'open_in_new')
                            ])
                        ]),
                        m('button.red.secondary.compact', {
                            onclick: e => {
                                let didDelete = deleteFile(data.uri)
                            }
                        }, [
                            m('.material-symbols-rounded', 'delete')
                        ]),
                        m('button.secondary.file__mobile-context.compact', {
                            onclick: e => {FileContext.openWith(data, vnode.dom)}
                        }, [
                            m('.material-symbols-rounded', 'more_vert')
                        ])
                    ])
                ]),
                m('.file__thumbnail--cell', {
                    style: `background-image: url('${data.thumbnail}')`
                }),
                m('.file__data--cell', [
                    m('.file__title--cell', [
                        m('h2', data.filename),
                        m('input', {
                            onblur: e => {
                                if (e.target.value != data.filename) {
                                    renameFile(data.uri, e.target.value)
                                }
                            },
                            value: data.filename
                        })
                    ]),
                    m('small', `${data.uploaded_at} • ${data.size_mb}MB`)
                ])
            ])
            case 'table':
            return m('tr.file--row', [
                m('td', [
                    m('.material-symbols-rounded.file__icon', 'draft')
                ]),
                m('td.file__title--row', [
                    m('span', data.filename),
                    m('input', {
                        onblur: e => {
                            if (e.target.value != data.filename) {
                                renameFile(data.uri, e.target.value)
                            }
                        },
                        value: data.filename
                    })
                ]),
                m('td.file__size--row', `${data.size_mb}MB`),
                m('td.file__date--row', data.uploaded_at),
                m('td', [
                    m('.buttons', [
                        m('button.white.secondary.compact', {
                            onclick: e => {
                                navigator.clipboard.writeText(data.url)
                                this.didCopy = true
                            }
                        }, [
                            m('.material-symbols-rounded', this.didCopy ? 'check' : 'content_copy')
                        ]),
                        m('a', {
                            href: data.url,
                            target: '_blank',
                            rel: 'noopener noreferrer'
                        }, [
                            m('button.white.secondary.compact', [
                                m('.material-symbols-rounded', 'open_in_new')
                            ])
                        ]),
                        m('button.red.secondary.compact', {
                            onclick: e => {
                                let didDelete = deleteFile(data.uri)
                            }
                        }, [
                            m('.material-symbols-rounded', 'delete')
                        ]),
                        m('button.secondary.file__mobile-context.compact', {
                            onclick: e => {FileContext.openWith(data, vnode.dom)}
                        }, [
                            m('.material-symbols-rounded', 'more_vert')
                        ])
                    ])
                ])
            ])
        }
    }
}

var Files = Files || {
    showTitle: true,
    shouldLoad: true,
    displayMode: 'table',
    typingTimeout: null,
    dead: false,
    loading: false,
    pos: 0,
    query: '',
    oninit() {
        files = []
        this.loadFiles()
        this.queueFiles()
    },
    queueFiles() {
        if (!this.dead && isAtBottom() && !this.loading) {
            this.loadFiles()
        }
        setTimeout(() => this.queueFiles(), 500)
    },
    setQuery(query) {
        this.query = query || '*'
        clearTimeout(this.typingTimeout)
        this.typingTimeout = setTimeout(() => {
            files = []
            this.dead = false
            this.pos = 0
            this.loadFiles(true)
        }, 300)
    },
    loadFiles(empty=false) {
        if (empty) {
            files = []
            this.dead = false
            this.pos = 0
        }

        this.loading = true
        m.request({url: `/files/get?pos=${this.pos}&query=*${this.query}*`})
            .then(res => {
                const len = res.length
                if (len == 0) {
                    this.dead = true
                    return
                }
                files = files.concat(res)
                this.pos += len
                this.loading = false
                m.redraw()
            })
    },
    view() {
        return [
            m(FileContext),
            m('.files__head', [
                this.showTitle ? m('h1.files__title', t('My files')) : null,
                m('input.files__search', {
                    placeholder: t('Search for files'),
                    oninput: e => this.setQuery(e.target.value)
                }),
                m('.buttons', [
                    m('button', {
                        onclick: () => {this.displayMode = this.displayMode == 'grid' ? 'table' : 'grid'}
                    }, [
                        m('.material-symbols-rounded', this.displayMode == 'grid' ? 'lists' : 'grid_view')
                    ])
                ])
            ]),
            this.displayMode == 'grid'
                ? m('.files--grid', files.map(file => m(FileRecord, {data: file, display: this.displayMode})))
                : m('table.files--table', [
                    m('thead', [
                        m('th', {style: 'width: 0'}),
                        m('th', t('Name')),
                        m('th', t('Size')),
                        m('th.files__header--table', t('Upload date')),
                        m('th', {style: 'width: 0'})
                    ]),
                    m('tbody', files.map(file => m(FileRecord, {data: file, display: this.displayMode})))
                ]),
            // m('span', {disabled: !this.dead ? 'true' : ''}, this.dead ? 'No more results' : 'Loading files...')
        ]
    }
}

function isAtBottom() {
    return (window.innerHeight + window.scrollY) >= document.body.offsetHeight - 200
}