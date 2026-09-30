import re

# 1. HTML modifications
with open(r'aegis/aegis/frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the send-arrow span
html = re.sub(r'<span class="send-arrow">.*?</span>', '', html)

with open(r'aegis/aegis/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 2. CSS modifications
with open(r'aegis/aegis/frontend/styles.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Update mic height and width and border radius to 54px / 15px
css = css.replace('width: 44px !important;', 'width: 54px !important;')
css = css.replace('height: 44px !important;', 'height: 54px !important;')
css = css.replace('border-radius: 12px !important;', 'border-radius: 15px !important;')

# To ensure the send button text centers perfectly, add justify-content to the end of styles.css
css += '\n.send-button { justify-content: center !important; }\n'

with open(r'aegis/aegis/frontend/styles.css', 'w', encoding='utf-8') as f:
    f.write(css)

print("Alignment fixed.")
