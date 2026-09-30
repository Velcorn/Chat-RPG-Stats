"""Write a small shields-style SVG badge: python badge.py LABEL VALUE COLOR OUT.svg

The coverage badge is made in CI and kept on its own branch, so main gets no extra commits and no service
(shields.io, Codecov) needs access to the repo.
"""
import sys
from html import escape


def badge(label: str, value: str, color: str) -> str:
    # Verdana 11px is about 7 px per character; 10 px padding around each text.
    lw, vw = 7 * len(label) + 10, 7 * len(value) + 10
    w = lw + vw
    text = f"{escape(label)}: {escape(value)}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="{text}">\n'
        '<linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
        '<stop offset="1" stop-opacity=".1"/></linearGradient>\n'
        f'<clipPath id="r"><rect width="{w}" height="20" rx="3" fill="#fff"/></clipPath>\n'
        f'<g clip-path="url(#r)"><rect width="{lw}" height="20" fill="#555"/>'
        f'<rect x="{lw}" width="{vw}" height="20" fill="{color}"/><rect width="{w}" height="20" fill="url(#s)"/></g>\n'
        '<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">\n'
        f'<text x="{lw / 2}" y="14">{escape(label)}</text><text x="{lw + vw / 2}" y="14">{escape(value)}</text></g>\n'
        "</svg>\n"
    )


if __name__ == "__main__":
    label, value, color, out = sys.argv[1:5]
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(badge(label, value, color))
