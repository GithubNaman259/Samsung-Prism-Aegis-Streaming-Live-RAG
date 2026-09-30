import re

with open(r'aegis/aegis/frontend/index.html', 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

# Extract the mic button block
mic_pattern = r'(<button[^>]*id="mic"[^>]*>.*?</button>)'
mic_match = re.search(mic_pattern, html, flags=re.DOTALL)

if mic_match:
    mic_html = mic_match.group(1)
    
    # Remove it from its current location
    html = html.replace(mic_html, '')
    
    # Find the send button
    send_pattern = r'(<button id="send" class="send-button">.*?<\/button>)'
    send_match = re.search(send_pattern, html, flags=re.DOTALL)
    
    if send_match:
        send_html = send_match.group(1)
        # Wrap both in a flex container to keep them side by side
        new_buttons = f'<div style="display: flex; gap: 8px; align-items: center;">\n{mic_html}\n{send_html}\n</div>'
        html = html.replace(send_html, new_buttons)

    with open(r'aegis/aegis/frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Mic button moved next to Send.")
else:
    print("Could not find mic button.")
