with open(r'aegis/aegis/frontend/styles.css', 'a', encoding='utf-8') as f:
    f.write('''
/* === BRUTE FORCE ALIGNMENT === */
.composer-row {
    align-items: center !important;
}
.input-wrap {
    height: 54px !important;
    display: flex !important;
}
.input-wrap input {
    height: 54px !important;
    box-sizing: border-box !important;
    margin: 0 !important;
}
#mic {
    height: 54px !important;
    width: 54px !important;
    box-sizing: border-box !important;
    margin: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}
#send {
    height: 54px !important;
    box-sizing: border-box !important;
    margin: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}
''')
print("Brute force alignment CSS appended.")
