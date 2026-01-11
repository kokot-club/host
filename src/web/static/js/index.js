// localization utility
var languageCache = {}

function getLanguage() {
    const saved = localStorage.getItem('lang')
    const lang = saved || 'en'
    if (!saved) {
        localStorage.setItem('lang', lang)
    }

    return lang
}

function loadLanguage(lang) {
    if (!languageCache[lang]) {
      var req = new XMLHttpRequest()
      req.open('GET', '/static/lang/' + lang + '.json', false)
      req.send(null)

      var txt = req.responseText || ''

      if (req.status === 200) {
          try {
              languageCache[lang] = JSON.parse(txt)
          } catch (e) {
              languageCache[lang] = {}
          }
      } else {
          languageCache[lang] = {}
      }
    }
    return languageCache[lang]
}

function t(str) {
    var dict = loadLanguage(getLanguage())
    return dict[str] || str
}

// color schema manager
const root = document.documentElement
let saved = localStorage.getItem('theme')

if (!saved) {
    saved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    localStorage.setItem('theme', saved)
}

root.dataset.theme = saved
