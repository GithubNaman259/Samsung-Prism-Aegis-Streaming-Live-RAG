import re

# 1. Patch HTML
with open(r'aegis/aegis/frontend/index.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

# Replace whatever mic button is there with the original wave structure
pattern = r'(<button[^>]*id="mic"[^>]*>)(.*?)(</button>)'
replacement = r'''\1
    <img src="/static/mic.png" alt="mic" class="mic-img" style="height: 22px; width: auto; object-fit: contain;">
    <span class="wave wave-a"></span>
    <span class="wave wave-b"></span>
    <span class="wave wave-c"></span>
\3'''
html = re.sub(pattern, replacement, html, flags=re.DOTALL)
with open(r'aegis/aegis/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 2. Patch CSS
# Remove any custom wave-container or mic CSS from the file
with open(r'aegis/aegis/frontend/styles.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Truncate at /* === MIC & WAVE ANIMATIONS === */ if it exists
index = css.find('/* === MIC & WAVE ANIMATIONS === */')
if index != -1:
    css = css[:index]

# Add back only the specific overrides needed for the button itself (not the waves, since waves are in base CSS!)
# Actually, the base CSS already contains the perfect wave animation!
# We just need to make sure the mic button styling fits the image nicely.
mic_css = '''
/* === MIC BUTTON LAYOUT === */
#mic {
    position: relative !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 44px !important;
    height: 44px !important;
    border-radius: 12px !important;
    background: rgba(7, 140, 255, 0.1) !important;
    border: 1px solid rgba(7, 140, 255, 0.3) !important;
    cursor: pointer !important;
    padding: 0 !important;
}
#mic.live {
    background: rgba(255, 107, 122, 0.15) !important;
    border-color: rgba(255, 107, 122, 0.5) !important;
}
#mic.live .mic-img {
    filter: brightness(0) saturate(100%) invert(43%) sepia(87%) saturate(2331%) hue-rotate(330deg) brightness(101%) contrast(106%) !important;
}
'''
css += mic_css

with open(r'aegis/aegis/frontend/styles.css', 'w', encoding='utf-8') as f:
    f.write(css)

print("Original wave animation restored.")
