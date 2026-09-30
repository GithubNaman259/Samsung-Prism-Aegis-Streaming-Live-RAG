with open(r'aegis/aegis/frontend/styles.css', 'a', encoding='utf-8') as f:
    f.write('''
/* === EXTRA BULLETPROOF ALIGNMENT === */
.input-wrap, .input-wrap input, #mic, #send {
    max-height: 54px !important;
    min-height: 54px !important;
    line-height: normal !important;
}
''')
print("Bulletproof CSS appended.")
