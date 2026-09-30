with open(r'aegis/aegis/frontend/styles.css', 'a', encoding='utf-8') as f:
    f.write('''

/* Massive Font Size Overrides for Readability */
.demo-button span { font-size: 16px !important; }
.demo-button b { font-size: 18px !important; }
.demo-button small { font-size: 14px !important; line-height: 1.4 !important; }

.metric .mv { font-size: 24px !important; }
.metric .ml { font-size: 14px !important; }

.dec { font-size: 16px !important; padding: 12px 0 !important; }
.dec .dt { font-size: 14px !important; }
.dec .dd { font-size: 16px !important; }
.dec .dr { font-size: 16px !important; }

#live-help { font-size: 16px !important; color: #a8d5ff !important; }
.composer-meta span { font-size: 16px !important; }

.activity-copy span { font-size: 16px !important; letter-spacing: 1px !important; }
.activity-copy strong { font-size: 18px !important; margin-left: 8px !important; }
small#spec-detail, .activity-item small { font-size: 15px !important; color: #9bcaff !important; margin-top: 6px !important; display: block; }

.timeline-label { font-size: 16px !important; }
#timeline-count { font-size: 16px !important; }

.empty-orb { width: 60px !important; height: 60px !important; }
.answer-empty p { font-size: 18px !important; line-height: 1.6 !important; margin-top: 20px !important; }

/* Composer Input fixes */
.composer-row {
    display: flex !important;
    gap: 16px !important;
    align-items: center !important;
}
.send-button {
    height: 50px !important;
    font-size: 18px !important;
    padding: 0 24px !important;
    border-radius: 12px !important;
}

/* Mic Button Fixes */
#mic {
    transition: all 0.2s ease !important;
}
#mic:hover {
    background: rgba(7, 140, 255, 0.2) !important;
    border-color: rgba(7, 140, 255, 0.6) !important;
}
#mic.live .mic-emoji {
    display: none !important;
}
#mic.live .wave-container {
    display: flex !important;
}
.wave {
    width: 6px !important;
    background: var(--red) !important;
    border-radius: 6px !important;
}
.wave-a { height: 16px !important; animation: waveBar 0.8s ease-in-out infinite !important; }
.wave-b { height: 26px !important; animation: waveBar 0.8s ease-in-out infinite 0.1s !important; }
.wave-c { height: 18px !important; animation: waveBar 0.8s ease-in-out infinite 0.2s !important; }

@keyframes waveBar {
    0%, 100% { transform: scaleY(0.4); }
    50% { transform: scaleY(1.2); }
}

/* Remove the old mic styles that were causing weird Q symbols */
.mic-icon { display: none !important; }
.icon-button.live .wave { animation: none !important; }
''')
print("Injected CSS fixes")
