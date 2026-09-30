with open(r'aegis/aegis/frontend/styles.css', 'r', encoding='utf-8') as f:
    content = f.read()

index = content.find('/* === GLOBAL TYPOGRAPHY === */')
if index != -1:
    content = content[:index]
    with open(r'aegis/aegis/frontend/styles.css', 'w', encoding='utf-8') as f:
        f.write(content)
    print("CSS truncated successfully.")
else:
    print("Could not find the injection point.")
