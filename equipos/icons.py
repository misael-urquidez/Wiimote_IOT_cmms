ICONOS_SVG = {
    "Solder Paste Printer": '''
    <svg viewBox="0 0 200 160" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="metalSPP" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#9aa3ab"/>
                <stop offset="100%" stop-color="#5b6470"/>
            </linearGradient>
        </defs>
        <rect x="20" y="120" width="160" height="14" rx="3" fill="#2b2f33"/>
        <rect x="35" y="20" width="130" height="80" rx="4" fill="url(#metalSPP)" stroke="#23272b" stroke-width="2"/>
        <rect x="45" y="32" width="110" height="50" fill="#2b2f33"/>
        <g stroke="#7f8a93" stroke-width="1.5">
            <line x1="50" y1="40" x2="150" y2="40"/>
            <line x1="50" y1="48" x2="150" y2="48"/>
            <line x1="50" y1="56" x2="150" y2="56"/>
            <line x1="50" y1="64" x2="150" y2="64"/>
            <line x1="50" y1="72" x2="150" y2="72"/>
        </g>
        <rect x="55" y="78" width="90" height="6" rx="2" fill="#e67e22"/>
        <rect x="20" y="100" width="160" height="10" fill="#3a3f44"/>
        <circle cx="45" cy="134" r="8" fill="#1c1f22"/>
        <circle cx="155" cy="134" r="8" fill="#1c1f22"/>
        <rect x="25" y="22" width="10" height="78" fill="#3a3f44"/>
        <rect x="165" y="22" width="10" height="78" fill="#3a3f44"/>
    </svg>
    ''',

    "Pick & Place": '''
    <svg viewBox="0 0 200 160" xmlns="http://www.w3.org/2000/svg">
        <rect x="15" y="125" width="170" height="12" rx="3" fill="#2b2f33"/>
        <rect x="25" y="30" width="150" height="10" fill="#6c7680"/>
        <rect x="20" y="20" width="10" height="100" fill="#4a525a"/>
        <rect x="170" y="20" width="10" height="100" fill="#4a525a"/>
        <rect x="60" y="38" width="14" height="55" fill="#8a93a0"/>
        <rect x="48" y="34" width="38" height="10" rx="2" fill="#aab3bd"/>
        <circle cx="67" cy="98" r="6" fill="#3498db"/>
        <line x1="67" y1="93" x2="67" y2="104" stroke="#1c1f22" stroke-width="2"/>
        <rect x="30" y="105" width="140" height="14" fill="#23272b"/>
        <circle cx="40" cy="112" r="4" fill="#e74c3c"/>
        <circle cx="55" cy="112" r="4" fill="#2ecc71"/>
        <circle cx="70" cy="112" r="4" fill="#f1c40f"/>
        <g fill="#555">
            <rect x="100" y="106" width="20" height="12" rx="2"/>
            <rect x="125" y="106" width="20" height="12" rx="2"/>
            <rect x="150" y="106" width="15" height="12" rx="2"/>
        </g>
    </svg>
    ''',

    "Horno Reflow": '''
    <svg viewBox="0 0 200 160" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="ovenBody" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#7a828a"/>
                <stop offset="100%" stop-color="#454b51"/>
            </linearGradient>
        </defs>
        <rect x="15" y="35" width="170" height="60" rx="8" fill="url(#ovenBody)" stroke="#23272b" stroke-width="2"/>
        <rect x="0" y="58" width="20" height="12" fill="#2b2f33"/>
        <rect x="180" y="58" width="20" height="12" fill="#2b2f33"/>
        <g>
            <rect x="28" y="55" width="20" height="18" fill="#c0392b" opacity="0.85"/>
            <rect x="55" y="55" width="20" height="18" fill="#e67e22" opacity="0.85"/>
            <rect x="82" y="55" width="20" height="18" fill="#f1c40f" opacity="0.85"/>
            <rect x="109" y="55" width="20" height="18" fill="#e67e22" opacity="0.85"/>
            <rect x="136" y="55" width="20" height="18" fill="#c0392b" opacity="0.85"/>
        </g>
        <line x1="20" y1="64" x2="180" y2="64" stroke="#1c1f22" stroke-width="3"/>
        <rect x="15" y="95" width="170" height="10" fill="#2b2f33"/>
        <circle cx="30" cy="115" r="7" fill="#1c1f22"/>
        <circle cx="170" cy="115" r="7" fill="#1c1f22"/>
        <rect x="160" y="20" width="22" height="14" rx="2" fill="#23272b"/>
        <text x="171" y="30" font-size="9" text-anchor="middle" fill="#2ecc71" font-family="monospace">245°C</text>
    </svg>
    ''',

    "Cinta Transportadora": '''
    <svg viewBox="0 0 200 160" xmlns="http://www.w3.org/2000/svg">
        <rect x="20" y="70" width="160" height="22" fill="#3a3f44" stroke="#23272b" stroke-width="2"/>
        <g stroke="#1c1f22" stroke-width="2">
            <line x1="30" y1="70" x2="22" y2="92"/>
            <line x1="50" y1="70" x2="42" y2="92"/>
            <line x1="70" y1="70" x2="62" y2="92"/>
            <line x1="90" y1="70" x2="82" y2="92"/>
            <line x1="110" y1="70" x2="102" y2="92"/>
            <line x1="130" y1="70" x2="122" y2="92"/>
            <line x1="150" y1="70" x2="142" y2="92"/>
            <line x1="170" y1="70" x2="162" y2="92"/>
        </g>
        <circle cx="30" cy="100" r="12" fill="#23272b" stroke="#555" stroke-width="2"/>
        <circle cx="170" cy="100" r="12" fill="#23272b" stroke="#555" stroke-width="2"/>
        <circle cx="30" cy="100" r="3" fill="#888"/>
        <circle cx="170" cy="100" r="3" fill="#888"/>
        <rect x="22" y="112" width="156" height="8" fill="#23272b"/>
        <rect x="60" y="55" width="30" height="14" rx="2" fill="#888"/>
        <rect x="100" y="58" width="22" height="10" rx="2" fill="#aaa"/>
    </svg>
    ''',

    "AOI": '''
    <svg viewBox="0 0 200 160" xmlns="http://www.w3.org/2000/svg">
        <rect x="30" y="110" width="140" height="14" rx="3" fill="#2b2f33"/>
        <rect x="40" y="30" width="12" height="85" fill="#6c7680"/>
        <rect x="148" y="30" width="12" height="85" fill="#6c7680"/>
        <rect x="35" y="24" width="130" height="10" fill="#4a525a"/>
        <rect x="85" y="34" width="30" height="40" fill="#8a93a0"/>
        <circle cx="100" cy="80" r="16" fill="#23272b" stroke="#555" stroke-width="2"/>
        <circle cx="100" cy="80" r="9" fill="#3498db"/>
        <circle cx="100" cy="80" r="4" fill="#aee3ff"/>
        <g stroke="#f1c40f" stroke-width="2" opacity="0.7">
            <line x1="100" y1="96" x2="92" y2="108"/>
            <line x1="100" y1="96" x2="108" y2="108"/>
            <line x1="100" y1="96" x2="100" y2="110"/>
        </g>
        <rect x="60" y="115" width="80" height="6" fill="#2ecc71" opacity="0.6"/>
    </svg>
    ''',

    "Flying Probe / ICT": '''
    <svg viewBox="0 0 200 160" xmlns="http://www.w3.org/2000/svg">
        <rect x="20" y="115" width="160" height="12" rx="3" fill="#2b2f33"/>
        <rect x="30" y="20" width="10" height="95" fill="#4a525a"/>
        <rect x="160" y="20" width="10" height="95" fill="#4a525a"/>
        <rect x="25" y="20" width="150" height="8" fill="#6c7680"/>
        <rect x="60" y="100" width="80" height="15" fill="#1c1f22"/>
        <g stroke="#aab3bd" stroke-width="2">
            <line x1="70" y1="100" x2="64" y2="40"/>
            <line x1="90" y1="100" x2="85" y2="32"/>
            <line x1="110" y1="100" x2="113" y2="36"/>
            <line x1="130" y1="100" x2="135" y2="44"/>
        </g>
        <g fill="#e74c3c">
            <circle cx="64" cy="38" r="4"/>
            <circle cx="85" cy="30" r="4"/>
            <circle cx="113" cy="34" r="4"/>
            <circle cx="135" cy="42" r="4"/>
        </g>
        <rect x="55" y="108" width="90" height="5" fill="#27ae60"/>
    </svg>
    ''',

    "Selective Soldering": '''
    <svg viewBox="0 0 200 160" xmlns="http://www.w3.org/2000/svg">
        <rect x="20" y="115" width="160" height="12" rx="3" fill="#2b2f33"/>
        <rect x="40" y="20" width="10" height="95" fill="#4a525a"/>
        <rect x="35" y="20" width="120" height="8" fill="#6c7680"/>
        <rect x="90" y="28" width="10" height="40" fill="#8a93a0"/>
        <path d="M85 68 h20 l-6 28 a8 8 0 0 1 -8 0 z" fill="#e67e22" stroke="#a85a16" stroke-width="1.5"/>
        <circle cx="95" cy="100" r="4" fill="#f1c40f"/>
        <rect x="60" y="108" width="70" height="7" fill="#2c3e50"/>
        <rect x="130" y="40" width="22" height="18" rx="2" fill="#888"/>
        <circle cx="141" cy="49" r="3" fill="#2ecc71"/>
    </svg>
    ''',
}

ICONO_DEFAULT = '''
    <svg viewBox="0 0 200 160" xmlns="http://www.w3.org/2000/svg">
        <rect x="40" y="40" width="120" height="80" rx="8" fill="#555" stroke="#333" stroke-width="2"/>
        <text x="100" y="95" font-size="40" text-anchor="middle" fill="#222">?</text>
    </svg>
'''