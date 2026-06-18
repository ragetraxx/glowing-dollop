import requests
import argparse
import pyperclip
import sys
import time
import random
from lxml import etree

# ── ANSI escape codes ────────────────────────────────────────
G   = '\033[92m'   # bright green
DG  = '\033[32m'   # dark green
CY  = '\033[96m'   # cyan
YL  = '\033[93m'   # yellow
RD  = '\033[91m'   # red
DM  = '\033[2m'    # dim
BD  = '\033[1m'    # bold
RS  = '\033[0m'    # reset

BANNER = [
    " __  __     _     _   _ ___      _____  ____      _      ____ _  __ ____  ",
    "|  \\/  |   / \\   | \\ | |_ _|    |_   _||  _ \\    / \\    / ___| |/ // ___|",
    "| |\\/| |  / _ \\  |  \\| || |       | |  | |_) |  / _ \\  | |   | ' /\\___ \\",
    "| |  | | / ___ \\ | |\\  || |       | |  |  _ <  / ___ \\ | |___| . \\ ___) |",
    "|_|  |_|/_/   \\_\\|_| \\_|___|      |_|  |_| \\_\\/_/   \\_\\ \\____|_|\\_\\____/ ",
]

_GC = r"!@#$%^&*()_+-=[]{}|;,.<>?/\~`ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def _glitch_reveal():
    w    = max(len(l) for l in BANNER)
    pad  = [l.ljust(w) for l in BANNER]
    n    = len(BANNER)
    cur  = [[random.choice(_GC) for _ in range(w)] for _ in range(n)]
    pos  = [(r, c) for r in range(n) for c in range(w)]
    random.shuffle(pos)
    steps = 14
    chunk = max(1, len(pos) // steps)
    done  = [[False] * w for _ in range(n)]

    sys.stdout.write('\033[?25l')  # hide cursor
    for step in range(steps + 1):
        for r, c in pos[step * chunk: min((step + 1) * chunk, len(pos))]:
            done[r][c] = True
        for r in range(n):
            for c in range(w):
                if not done[r][c]:
                    cur[r][c] = random.choice(_GC)
        if step > 0:
            sys.stdout.write(f'\033[{n}A')
        for r in range(n):
            row = ''
            for c in range(w):
                ch = pad[r][c]
                row += (f'{BD}{G}{ch}{RS}' if done[r][c] else f'{DG}{cur[r][c]}{RS}')
            sys.stdout.write(row + '\n')
        sys.stdout.flush()
        time.sleep(0.04)
    sys.stdout.write('\033[?25h')  # show cursor


def show_banner():
    print()
    _glitch_reveal()
    time.sleep(0.08)

    subtitle = '  MPD manifest track & KID extractor'
    sys.stdout.write(f'\n{CY}')
    for ch in subtitle:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(0.018)
    sys.stdout.write(RS + '\n')

    tag = f'  by th3magpi3  ::  v1.0  ::  2026'
    sys.stdout.write(f'{DM}  by {RS}{G}th3magpi3{RS}{DM}  ::  v1.0  ::  2026{RS}\n')
    sys.stdout.write(f'{DG}  {"─" * (len(tag) - 2)}{RS}\n\n')
    sys.stdout.flush()


def get_mpd_content(input_path):
    if input_path.startswith(('http://', 'https://')):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(input_path, headers=headers)
        response.raise_for_status()
        return response.content
    with open(input_path, 'rb') as f:
        return f.read()


def parse_mpd(xml_content):
    ns   = {'dash': 'urn:mpeg:dash:schema:mpd:2011', 'cenc': 'urn:mpeg:cenc:2013'}
    root = etree.fromstring(xml_content)
    rows = []

    for ad_set in root.xpath('//dash:AdaptationSet', namespaces=ns):
        content_type = ad_set.get('contentType')
        if not content_type:
            mime = ad_set.get('mimeType', '')
            if 'video' in mime:    content_type = 'video'
            elif 'audio' in mime:  content_type = 'audio'
            else:                  content_type = 'data'

        kid_xpath = './/dash:ContentProtection[@cenc:default_KID]/@cenc:default_KID'
        kid_list  = ad_set.xpath(kid_xpath, namespaces=ns)
        kid_val   = kid_list[0] if kid_list else 'No KID Found'

        for rep in ad_set.xpath('.//dash:Representation', namespaces=ns):
            bitrate     = rep.get('bandwidth', '0')
            width       = rep.get('width')
            height      = rep.get('height')
            res_or_lang = f"{width}x{height}" if (width and height) else ad_set.get('lang', 'und')
            rows.append((content_type, res_or_lang, bitrate, kid_val))

    return rows


def _plain_table(rows):
    lines = [f"{'TYPE':<10} | {'RES/LANG':<12} | {'BITRATE':<10} | {'KID'}", '-' * 85]
    for ct, rl, br, kid in rows:
        lines.append(f"{ct:<10} | {rl:<12} | {br:<10} | {kid}")
    return '\n'.join(lines)


def _print_colored_table(rows):
    print(f'{BD}{CY}{"TYPE":<10} | {"RES/LANG":<12} | {"BITRATE":<10} | {"KID"}{RS}')
    print(f'{DG}{"─" * 85}{RS}')
    for ct, rl, br, kid in rows:
        tc = G  if ct == 'video' else (YL if ct == 'audio' else DM)
        kc = G  if kid != 'No KID Found' else RD
        print(f'{tc}{ct:<10}{RS} | {rl:<12} | {DM}{br:<10}{RS} | {kc}{kid}{RS}')


def main():
    parser = argparse.ArgumentParser(description='mani-tracks — MPD manifest track & KID extractor')
    parser.add_argument('input', nargs='?', help='MPD URL or local file path')
    args = parser.parse_args()

    show_banner()

    target = args.input
    if not target:
        sys.stdout.write(f'{CY}  Enter MPD URL or file path:{RS} ')
        sys.stdout.flush()
        target = input().strip()
        print()

    try:
        content = get_mpd_content(target)
        rows    = parse_mpd(content)
        _print_colored_table(rows)
        plain   = _plain_table(rows)
        pyperclip.copy(plain)
        print(f'\n{G}✔ Results copied to clipboard!{RS}')
    except Exception as e:
        print(f'{RD}Error: {e}{RS}')


if __name__ == '__main__':
    main()
