with open(r'aegis/aegis/frontend/styles.css', 'a', encoding='utf-8') as f:
    f.write('''
#mic.live .wave-container {
    display: flex !important;
    gap: 4px !important;
    align-items: center !important;
    justify-content: center !important;
    height: 30px !important;
}
''')
print("Injected CSS fixes 2")
