var Files = Files || {}

var Home = Home || {
    totalUploads: 0,
    totalUsageGb: 0,
    latestUser: '',
    latestUid: 0,
    onremove() {
        Files.showTitle = true
    },
    oninit() {
        Files.showTitle = false
        m.request({url: '/analytics/server_storage'}).then(data => {
            this.totalUploads = data.total_uploads
            this.totalUsageGb = parseFloat(data.used_mb / 1000).toFixed(2)
        })

        const styles = getComputedStyle(document.documentElement)
        const chartAccent = styles.getPropertyValue('--accent').trim()
        const chartCrust = styles.getPropertyValue('--crust').trim()
        m.request({url: '/analytics/daily_uploads'}).then(data => {
            const dailyUploads = document.querySelector('canvas#uploads')
            new Chart(dailyUploads, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.data,
                        borderColor: chartAccent,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    elements: {
                        point: { radius: 0, hitRadius: 40 }
                    },
                    scales: {
                        x: {
                            grid: {
                                color: chartCrust
                            }
                        },
                        y: {
                            grid: {
                                color: chartCrust
                            },
                            beginAtZero: true,
                            ticks: {
                                minSuggested: 10,
                                stepSize: 20,
                            }
                        }
                    },
                    plugins: {
                        legend: { display: false },
                        title: { display: false }
                    }
                },
            })
        })

        m.request({url: '/analytics/userbase_info'}).then(data => {
            this.latestUser = data.latest_user
            this.latestUid = data.latest_uid

            const userChart = document.querySelector('canvas#users')
            new Chart(userChart, {
                type: 'line',
                data: {
                    labels: data.history.labels,
                    datasets: [{
                        data: data.history.data,
                        borderColor: chartAccent,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    elements: {
                        point: { radius: 0, hitRadius: 40 }
                    },
                    scales: {
                        x: {
                            grid: {
                                color: chartCrust
                            }
                        },
                        y: {
                            grid: {
                                color: chartCrust
                            },
                            beginAtZero: true,
                            ticks: {
                                minSuggested: 10,
                                stepSize: 10,
                                
                            }
                        }
                    },
                    plugins: {
                        legend: { display: false },
                        title: { display: false }
                    }
                },
            })
        })
    },
    view() {
        return [
            m('hgroup', [
                m('h1', t('Welcome to'), ' kokot host!'),
                m('p', t('Check out the web uploader and start sharing files. You may also set up integrations with our service')),
            ]),
            m('.grid', [
                m('.stat', [
                    m('small', t('All uploads')),
                    m('h1.stat__value', this.totalUploads)
                ]),
                m('.stat', [
                    m('small', t('Server storage usage')),
                    m('h1.stat__value', `${this.totalUsageGb}GB`)
                ]),
                m('.stat', [
                    m('small', t('Most recent user')),
                    m('h1.stat__value', `${this.latestUser} (UID: ${this.latestUid})`)
                ]),
            ]),
            m('.grid', [
                m('.chart', [
                    m('.chart__head', [
                        m('h3', t('Daily uploads'))
                    ]),
                    m('canvas#uploads')
                ]),
                m('.chart', [
                    m('.chart__head', [
                        m('h3', t('Registered users'))
                    ]),
                    m('canvas#users')
                ]),
            ]),
        ]
    }
}