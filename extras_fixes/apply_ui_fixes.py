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
        <img src="/static/mic.png" alt="mic" class="mic-img" style="width: 24px; height: 24px; filter: brightness(0) invert(1);">
    </div>
\3'''
html = re.sub(pattern, replacement, html, flags=re.DOTALL)
with open(r'aegis/aegis/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)


# 2. Patch JS
with open(r'aegis/aegis/frontend/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Replace the tag creation logic
js_pattern = r'if\(added\|\|mod\)\{const t=document\.createElement\("span"\);t\.className="status-tag";t\.textContent=added\?[^\}]+p\.appendChild\(t\)\}'
js_replacement = '''if(added||mod||(res.version > 1 && !added && !mod)){
      const t=document.createElement("span");
      t.className = "status-tag " + (added ? "new-tag" : (mod ? "patched-tag" : "reused-tag"));
      t.textContent = added ? "NEW" : (mod ? "PATCHED" : "REUSED");
      p.appendChild(t);
    }'''
js = re.sub(js_pattern, js_replacement, js)
with open(r'aegis/aegis/frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(js)


# 3. Patch CSS
css_additions = '''
/* === HIGHLIGHTS AND FONTS === */
.timeline-wrap {
    background: linear-gradient(180deg, rgba(7, 140, 255, 0.08), rgba(7, 140, 255, 0.02)) !important;
    border: 1px solid rgba(7, 140, 255, 0.3) !important;
    padding: 20px !important;
    border-radius: 12px !important;
    margin-bottom: 24px !important;
    box-shadow: 0 0 20px rgba(7, 140, 255, 0.15) !important;
}

#spec-item {
    background: linear-gradient(90deg, rgba(255, 199, 102, 0.15), transparent) !important;
    border-left: 4px solid #ffc766 !important;
    padding: 12px 16px !important;
    border-radius: 4px !important;
    box-shadow: -10px 0 20px -10px rgba(255, 199, 102, 0.3) !important;
}

#subqueries .chip {
    font-size: 15px !important;
    background: linear-gradient(135deg, rgba(66, 232, 160, 0.2), rgba(66, 232, 160, 0.05)) !important;
    border: 1px solid rgba(66, 232, 160, 0.5) !important;
    color: #42e8a0 !important;
    padding: 10px 18px !important;
    border-radius: 20px !important;
    box-shadow: 0 4px 15px rgba(66, 232, 160, 0.15) !important;
    margin-right: 10px !important;
}

/* === CLAIM STATUS TAGS === */
.status-tag {
    font-size: 12px !important;
    font-weight: 800 !important;
    padding: 4px 10px !important;
    border-radius: 8px !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    display: inline-block !important;
    margin-left: 12px !important;
}
.status-tag.new-tag {
    color: #42e8a0 !important;
    background: rgba(66, 232, 160, 0.2) !important;
    border: 1px solid #42e8a0 !important;
}
.status-tag.patched-tag {
    color: #ffc766 !important;
    background: rgba(255, 199, 102, 0.2) !important;
    border: 1px solid #ffc766 !important;
}
.status-tag.reused-tag {
    color: #078cff !important;
    background: rgba(7, 140, 255, 0.2) !important;
    border: 1px solid #078cff !important;
}

/* === MIC & WAVE ANIMATIONS === */
#mic {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border: none !important;
    background: transparent !important;
    cursor: pointer !important;
    padding: 10px !important;
    transition: transform 0.2s !important;
}
#mic:hover {
    transform: scale(1.05) !important;
}
#mic.live .mic-img {
    filter: brightness(0) saturate(100%) invert(43%) sepia(87%) saturate(2331%) hue-rotate(330deg) brightness(101%) contrast(106%) !important; /* Turns it red */
}
#mic.live .wave-container {
    display: flex !important;
}

.wave {
    width: 4px !important;
    background: #ff6b7a !important;
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

print("UI fixes applied successfully.")
