with open(r'aegis/aegis/frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

bad_mic = '''              <button
                id="mic"
                class="icon-button"
                title="Voice input"
                aria-label="Voice input"
              >
                <span class="mic-icon"></span>
                <span class="wave wave-a"></span><span class="wave wave-b"></span
                ><span class="wave wave-c"></span>
              </button>'''

good_mic = '''              <button
                id="mic"
                class="icon-button"
                title="Voice input"
                aria-label="Voice input"
              >
                <svg class="mic-icon-svg" viewBox="0 0 24 24">
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="22"></line>
                </svg>
                <div class="wave-container">
                    <span class="wave wave-a"></span>
                    <span class="wave wave-b"></span>
                    <span class="wave wave-c"></span>
                </div>
              </button>'''

html = html.replace(bad_mic, good_mic)
with open(r'aegis/aegis/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Patched index.html")
