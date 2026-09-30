with open(r'aegis/aegis/frontend/styles.css', 'a') as f:
    f.write('''
#subqueries {
    transition: all 0.3s ease !important;
}
.query-area {
    background: rgba(0, 0, 0, 0.2) !important;
    padding: 16px !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    margin-bottom: 24px !important;
}
.mini-head {
    font-size: 13px !important;
    letter-spacing: 1.5px !important;
    color: #b8c0d0 !important;
    margin-bottom: 12px !important;
}
''')
print("Appended more CSS overrides")
