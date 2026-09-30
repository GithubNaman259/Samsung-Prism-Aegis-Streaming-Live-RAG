import os

css_overrides = '''

/* === GLOBAL TYPOGRAPHY === */
body {
    font: 18px/1.65 Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}
.answer {
    font-size: 19px !important;
    line-height: 1.8 !important;
}
input#query {
    font-size: 18px !important;
    padding: 18px 24px !important;
}
.placeholder, .hint, .composer-meta { 
    font-size: 14px !important; 
}

/* === TIMELINE AND SPECULATIVE HIGHLIGHTS === */
.timeline-wrap {
    background: linear-gradient(180deg, rgba(7, 140, 255, 0.08), rgba(7, 140, 255, 0.02)) !important;
    border: 1px solid rgba(7, 140, 255, 0.3) !important;
    padding: 20px !important;
    border-radius: var(--radius-md) !important;
    margin-bottom: 24px !important;
    box-shadow: 0 0 20px rgba(7, 140, 255, 0.15), inset 0 0 10px rgba(7, 140, 255, 0.05) !important;
}
.timeline-label {
    font-size: 12px !important;
    letter-spacing: 1.5px !important;
    color: #a8d5ff !important;
}

#spec-item {
    background: linear-gradient(90deg, rgba(255, 199, 102, 0.15), transparent) !important;
    border-left: 4px solid var(--amber) !important;
    padding: 12px 16px !important;
    border-radius: 4px !important;
    box-shadow: -10px 0 20px -10px rgba(255, 199, 102, 0.3) !important;
}
#spec-time {
    color: var(--amber) !important;
    font-size: 18px !important;
    font-weight: bold !important;
    text-shadow: 0 0 12px rgba(255, 199, 102, 0.8) !important;
}

/* === SUB-QUERIES === */
#subqueries .chip {
    font-size: 15px !important;
    background: linear-gradient(135deg, rgba(66, 232, 160, 0.2), rgba(66, 232, 160, 0.05)) !important;
    border: 1px solid rgba(66, 232, 160, 0.5) !important;
    color: #42e8a0 !important;
    padding: 10px 18px !important;
    border-radius: 20px !important;
    box-shadow: 0 4px 15px rgba(66, 232, 160, 0.15) !important;
    animation: pop 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    margin-right: 10px !important;
}

/* === CLAIM STATUS VISUALS === */
.claim {
    font-size: 18px !important;
    padding: 20px 24px !important;
    margin-bottom: 18px !important;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0 !important;
    transition: transform 0.3s ease, box-shadow 0.3s ease !important;
    background: rgba(255, 255, 255, 0.02) !important;
}
.claim:hover {
    transform: translateX(4px) !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important;
}

.claim.added {
    background: linear-gradient(90deg, rgba(66, 232, 160, 0.12), rgba(66, 232, 160, 0.02)) !important;
    border-left: 4px solid var(--green) !important;
}
.claim.modified {
    background: linear-gradient(90deg, rgba(255, 199, 102, 0.12), rgba(255, 199, 102, 0.02)) !important;
    border-left: 4px solid var(--amber) !important;
}
.claim.uncertain {
    background: linear-gradient(90deg, rgba(255, 107, 122, 0.12), rgba(255, 107, 122, 0.02)) !important;
    border-left: 4px solid var(--red) !important;
}

/* Enhancing the dynamically added Status Tags in app.js */
.status-tag {
    font-size: 12px !important;
    font-weight: 800 !important;
    padding: 4px 10px !important;
    border-radius: 8px !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    display: inline-block !important;
    margin-left: 12px !important;
    vertical-align: middle !important;
}
.status-tag.new-tag {
    color: var(--green) !important;
    background: rgba(66, 232, 160, 0.2) !important;
    border: 1px solid var(--green) !important;
    box-shadow: 0 0 10px rgba(66, 232, 160, 0.3) !important;
}
.status-tag.patched-tag {
    color: var(--amber) !important;
    background: rgba(255, 199, 102, 0.2) !important;
    border: 1px solid var(--amber) !important;
    box-shadow: 0 0 10px rgba(255, 199, 102, 0.3) !important;
}
.status-tag.reused-tag {
    color: var(--blue) !important;
    background: rgba(7, 140, 255, 0.2) !important;
    border: 1px solid var(--blue) !important;
    box-shadow: 0 0 10px rgba(7, 140, 255, 0.3) !important;
}

/* === MIC & WAVE ANIMATIONS === */
#mic {
    width: 50px !important;
    height: 50px !important;
    border-radius: 25px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    position: relative !important;
    overflow: visible !important;
    background: rgba(7, 140, 255, 0.1) !important;
    border: 2px solid rgba(7, 140, 255, 0.4) !important;
    transition: all 0.3s ease !important;
}
#mic:hover {
    background: rgba(7, 140, 255, 0.2) !important;
    transform: scale(1.05) !important;
}
#mic.live {
    background: rgba(255, 107, 122, 0.15) !important;
    border-color: rgba(255, 107, 122, 0.5) !important;
    box-shadow: 0 0 20px rgba(255, 107, 122, 0.4) !important;
    animation: micPulse 1.5s infinite alternate !important;
}
.mic-icon-svg {
    width: 22px;
    height: 22px;
    fill: none;
    stroke: var(--blue);
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
    transition: stroke 0.3s ease;
}
#mic.live .mic-icon-svg {
    stroke: var(--red);
}

.wave-container {
    position: absolute;
    right: -30px;
    display: flex;
    gap: 3px;
    align-items: center;
    opacity: 0;
    transition: opacity 0.3s ease;
}
#mic.live .wave-container {
    opacity: 1;
}
.wave {
    position: relative !important;
    right: 0 !important;
    width: 4px !important;
    border-radius: 4px !important;
    background: var(--red) !important;
    opacity: 1 !important;
}
.wave-a { height: 12px !important; animation: waveBar 1.2s ease-in-out infinite !important; }
.wave-b { height: 20px !important; animation: waveBar 1.2s ease-in-out infinite 0.15s !important; }
.wave-c { height: 16px !important; animation: waveBar 1.2s ease-in-out infinite 0.3s !important; }

@keyframes micPulse {
    from { box-shadow: 0 0 10px rgba(255, 107, 122, 0.2); }
    to { box-shadow: 0 0 25px rgba(255, 107, 122, 0.6); }
}
@keyframes waveBar {
    0%, 100% { transform: scaleY(0.5); }
    50% { transform: scaleY(1.5); }
}
'''

with open(r'aegis/aegis/frontend/styles.css', 'a') as f:
    f.write(css_overrides)
print("CSS overrides appended.")
