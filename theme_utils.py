"""Small shared helpers for the Perch Current theme builder."""


def fish(palette):
    color = palette['accent']
    return (
        f'<g fill="none" stroke="{color}" stroke-width="2.6" '
        'stroke-linejoin="round" stroke-linecap="round">'
        '<path d="M4 11 L20 20 Q41 0 69 15 L80 25 L66 36 Q39 44 20 29 '
        'L4 40 L9 25 Z M30 12 L33 2 L39 8 L44 0 L49 8 L54 2 L60 12 '
        'M37 13 L42 33 M49 12 L54 34"/>'
        f'<circle cx="68" cy="22" r="1.8" fill="{color}" stroke="none"/></g>'
    )


def luminance(color):
    channels = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
    return sum(c * weight for c, weight in zip(linear, (.2126, .7152, .0722)))
