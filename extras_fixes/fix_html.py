import re
with open(r'aegis/aegis/frontend/index.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

# Extract everything before composer-row and after send button
pattern = r'(<div class="composer-row">)(.*?)(<button id="send" class="send-button">.*?<\/button>)'
replacement = r'''\1
    <div class="input-wrap" style="flex: 1; position: relative;">
        <span class="input-glow"></span>
        <input
        id="utterance"
        type="text"
        autocomplete="off"
        placeholder="Find a venue for 30 people in Pune and retrieve its cancellation policy..."
        style="width: 100%;"
        />
    </div>
    <div style="display: flex; gap: 10px; align-items: center;">
        <button
        id="mic"
        class="icon-button"
        title="Voice input"
        aria-label="Voice input"
        style="font-size: 24px; background: rgba(7, 140, 255, 0.1); border: 1px solid rgba(7, 140, 255, 0.3); border-radius: 12px; width: 50px; height: 50px; cursor: pointer; display: flex; align-items: center; justify-content: center;"
        >
        <span class="mic-emoji">??</span>
        <div class="wave-container" style="display: none; gap: 3px; align-items: center;">
            <span class="wave wave-a"></span>
            <span class="wave wave-b"></span>
            <span class="wave wave-c"></span>
        </div>
        </button>
        \3
    </div>'''

new_html = re.sub(pattern, replacement, html, flags=re.DOTALL)
with open(r'aegis/aegis/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)
print("Fixed HTML")
