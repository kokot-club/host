let modalsSpawned = 0

var Modal = Modal || {
    modals: [],
    spawn(title, content, minWidth) {
        const id = modalsSpawned.toString()

        this.modals.push({
            title: title,
            content: content,
            minWidth: minWidth || '200px',
            _id: id
        })
        modalsSpawned++
        m.redraw()
    },
    close(id) {
        this.modals = this.modals.filter(modal => modal._id != id)
        m.redraw()
    },
    closeAll() {
        this.modals = []
        m.redraw()
    },
    view() {
        return this.modals.map(modal => 
            m('.dialog', [
                m('.dialog__body', {
                    style: `min-width: ${modal.minWidth}`
                }, [
                    m('.dialog__nav', [
                        m('.dialog__title', modal.title),
                    ]),
                    m('.dialog__content', modal.content)
                ])
            ])
        )
    }
}
