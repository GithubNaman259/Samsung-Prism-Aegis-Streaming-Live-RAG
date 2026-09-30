import re

# 1. Patch HTML
with open(r'aegis/aegis/frontend/index.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

# Replace the mic button
pattern = r'(<button[^>]*id="mic"[^>]*>)(.*?)(</button>)'
replacement = r'''\1
    <div style="display: flex; align-items: center; gap: 8px;">
        <div class="wave-container" style="display: none; align-items: center; gap: 3px; height: 24px;">
            <span class="wave wave-a"></span>
            <span class="wave wave-b"></span>
            <span class="wave wave-c"></span>
        </div>
        <img src="/static/mic.png" alt="mic" class="mic-img" style="height: 22px; width: auto; object-fit: contain;">
    </div>
\3'''
html = re.sub(pattern, replacement, html, flags=re.DOTALL)
with open(r'aegis/aegis/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 2. Patch CSS
css_additions = '''
/* === MIC & WAVE ANIMATIONS === */
#mic {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 10px !important;
    background: transparent !important;
    border: none !important;
    cursor: pointer !important;
}

#mic.live .wave-container {
    display: flex !important;
}

.wave {
    width: 4px !important;
    background: #078cff !important;
    border-radius: 4px !important;
}
.wave-a { height: 12px !important; animation: waveBar 0.8s ease-in-out infinite !important; }
.wave-b { height: 22px !important; animation: waveBar 0.8s ease-in-out infinite 0.1s !important; }
.wave-c { height: 16px !important; animation: waveBar 0.8s ease-in-out infinite 0.2s !important; }

@keyframes waveBar {
    0%, 100% { transform: scaleY(0.4); }
    50% { transform: scaleY(1.2); }
}

/* Clear old wave CSS that might conflict */
.icon-button.live .wave { animation: none !important; }
'''

with open(r'aegis/aegis/frontend/styles.css', 'a', encoding='utf-8') as f:
    f.write(css_additions)

print("Mic UI fixes applied successfully.")
