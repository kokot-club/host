var FileJob = FileJob || {
    didCopy: false,
    view(vnode) {
        const job = vnode.attrs.job
        return m('.file-job', [
            m('.file-job__head', [
                m('.material-symbols-rounded', 'draft'),
                m('.file-job__data', [
                    m('h3.file-job__title', job.filename),
                    m('progress.file-job__progress', {
                        min: 0,
                        max: 100,
                        value: job.progress
                    })
                ])
            ]),
            m('.alert', {
                class: job.data ? (job.data.error ? 'alert--error' : '') : ''
            }, job.data ? [
                m('span', job.data.error ? `${t('Error uploading file')}: ${job.data.error}` : t('Your file is ready!')),
                !job.data.error ? m('.file-job__result', [
                    m('input.file-job__url', {
                        readonly: 'true',
                        value: job.data.url
                    }),
                    m('.buttons', [
                        m('button.white', {
                            onclick: e => {
                                navigator.clipboard.writeText(job.data.url)
                                this.didCopy = true
                            }
                        }, [
                            m('.material-symbols-rounded', this.didCopy ? 'check' : 'content_copy')
                        ]),
                        m('a.buttons', {
                            href: job.data.url,
                            target: '_blank',
                            rel: 'noopener noreferrer'
                        }, [
                            m('button', [
                                m('.material-symbols-rounded', 'open_in_new')
                            ])
                        ])
                    ])
                ]) : null
            ] : t('Uploading...'))
        ])
    }
}

var Uploader = Uploader || {
    files: [],
    jobs: [],
    fileInput: null,
    fileHovering: false,
    onsubmit(e) {
        e.preventDefault()

        const jobId = Date.now()
        const xhr = new XMLHttpRequest()
        const formData = new FormData()
        this.files.forEach(f => formData.append('file', f))

        const filenames = this.files.map(f => f.name).join(', ')
        const job = {id: jobId, progress: 0, filename: filenames}
        this.jobs.push(job)

        xhr.upload.addEventListener('progress', e => {
            if (e.lengthComputable) {
                job.progress = (e.loaded / e.total) * 100
                m.redraw()
            }
        })

        xhr.addEventListener('load', () => {
            job.progress = 100

            try {
                const data = JSON.parse(xhr.response)
                job.data = data

                Dashboard.updateStorageData()
            } catch (err) {
                // bad json
            }

            m.redraw()
        })

        xhr.open('POST', '/files/upload')
        xhr.send(formData)
    },
    view() {
        return m('div', {
            style: 'width: 100%; max-width: 1280px; margin-inline: auto'
        }, [
            m('.uploader', {
                class: this.fileHovering ? 'uploader--hover' : '',
                ondragover: e => {
                    e.preventDefault()
                    this.fileHovering = true
                },
                ondragleave: e => {
                    this.fileHovering = false
                },
                ondrop: e => {
                    e.preventDefault()
                    this.fileHovering = false
                    if (e.dataTransfer.types.includes('Files')) {
                        this.files = Array.from(e.dataTransfer.files).slice(0, 1)
                        this.onsubmit(e)
                    }
                }
            }, [
                m('.material-symbols-rounded.uploader__icon', 'stacks'),
                m('h3.uploader__title', t('Drag and Drop your files')),
                m('small', t('or')),
                m('button[type="button"]', {
                    onclick: e => {this.fileInput.click()}
                }, t('Browse files')),
                m('input[type=file].hidden', {
                    multiple: false,
                    oncreate: v => this.fileInput = v.dom,
                    onchange: e => {
                        this.files = Array.from(e.target.files)
                        this.onsubmit(e)
                    }
                })
            ]),
            m('.file-jobs', [
                this.jobs.map(job => m(FileJob, {job: job}))
            ])
        ])
    }
}