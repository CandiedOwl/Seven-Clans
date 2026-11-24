#!/usr/bin/env python3
"""Copy the Player Guide from the Obsidian vault into this Zola site.

Usage:
    python3 scripts/sync.py [path/to/vault]

The default vault path is ../Ancient-Darkness/Ancient Darkness, next to this repo.

Only notes in the vault's "Player Guide" folder are copied, plus the saved
player map. The script stops without writing anything if it finds:
  - a word from the spoiler list (see FORBIDDEN), or
  - a link to any note outside the Player Guide.
That keeps GM-only material out of this public repository.
"""
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_VAULT = ROOT.parent / "Ancient-Darkness" / "Ancient Darkness"

# Page order on the site. The first one becomes the home page.
ORDER = [
    "Player Guide",
    "How the World Works",
    "The Clans",
    "People of the Wolf",
    "People of the Raven",
    "People of the Seal",
    "People of the Owl",
    "People of the Auroch",
    "People of the Boar",
    "People of the Reindeer",
    "Customs and Beliefs",
    "Spirits of the World",
    "The Land",
    "Making a Character",
    "Custom Subclasses",
]

# Words that must never appear on the public site. Matching is case-insensitive.
FORBIDDEN = [
    r"soul-?eaters?", r"hollow", r"\botters?\b", r"\blutra\b", r"holt-keeper",
    r"\bfollowers?\b", r"marsh-chief", r"gm only", r"\[!danger\]", r"\bPCs?\b",
    r"\boskel\b", r"first binding", r"mid-boss", r"secret soul",
]

# Images may only come from this vault folder.
MARKS_DIR = pathlib.Path("Assets") / "Clan Marks"
IMAGE_EMBED = re.compile(r"!\[\[([^\]|]+\.svg)(?:\\?\|(\d+))?\]\]")

WIKILINK = re.compile(r"\[\[([^\]|#\\]+)(#[^\]|\\]+)?(?:\\?\|([^\]]+))?\]\]")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def target_path(name):
    return "_index.md" if name == ORDER[0] else slug(name) + ".md"


def strip_frontmatter(text):
    if text.startswith("---\n"):
        end = text.index("\n---\n", 4)
        return text[end + 5:]
    return text


def check_spoilers(label, text, problems):
    for pattern in FORBIDDEN:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            line = text.count("\n", 0, m.start()) + 1
            problems.append(f"{label}:{line}: forbidden word '{m.group(0)}'")


def convert_links(label, text, problems):
    def repl(m):
        name, anchor, alias = m.group(1).strip(), m.group(2), m.group(3)
        if name not in ORDER:
            problems.append(f"{label}: link to a note outside the Player Guide: [[{name}]]")
            return m.group(0)
        shown = alias or name
        frag = "#" + slug(anchor[1:]) if anchor else ""
        return f"[{shown}](@/{target_path(name)}{frag})"
    return WIKILINK.sub(repl, text)


def convert_images(label, text, vault, images, problems):
    def repl(m):
        name, width = m.group(1).strip(), m.group(2)
        src = vault / MARKS_DIR / name
        if not src.is_file():
            problems.append(f"{label}: image not found in {MARKS_DIR}: {name}")
            return m.group(0)
        images[slug(name[:-4]) + ".svg"] = src
        alt = name[:-4].replace(" Clan Mark", "")
        style = f' width="{width}" height="{width}"' if width else ""
        return f'<img class="clan-mark" src="../marks/{slug(name[:-4])}.svg" alt="Mark of the {alt} Clan"{style}>'
    return IMAGE_EMBED.sub(repl, text)


def main():
    vault = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_VAULT
    guide = vault / "Player Guide"
    map_src = vault / "Dashboards" / "Maps" / "Player Map.html"
    if not guide.is_dir():
        sys.exit(f"Can't find the Player Guide folder at {guide}")

    found = {p.stem for p in guide.glob("*.md")}
    missing = [n for n in ORDER if n not in found]
    extra = sorted(found - set(ORDER))
    if missing:
        sys.exit("These notes are listed in ORDER but missing from the vault: " + ", ".join(missing))

    problems, pages, images = [], {}, {}
    for weight, name in enumerate(ORDER):
        raw = (guide / f"{name}.md").read_text(encoding="utf-8")
        body = strip_frontmatter(raw).strip() + "\n"
        check_spoilers(f"{name}.md", body, problems)
        body = convert_images(f"{name}.md", body, vault, images, problems)
        body = convert_links(f"{name}.md", body, problems)
        if weight == 0:
            front = f'+++\ntitle = "{config_title()}"\nsort_by = "weight"\n+++\n\n'
        else:
            front = f'+++\ntitle = "{name}"\nweight = {weight}\n+++\n\n'
        pages[target_path(name)] = front + body

    for out_name, src in images.items():
        check_spoilers(src.name, src.read_text(encoding="utf-8"), problems)

    map_html = None
    if map_src.exists():
        map_html = map_src.read_text(encoding="utf-8")
        check_spoilers("Player Map.html", map_html, problems)
    else:
        problems.append(f"Player map not found at {map_src}")

    if problems:
        print("Sync stopped. Nothing was written. Fix these in the vault first:\n")
        print("\n".join("  - " + p for p in problems))
        sys.exit(1)

    content = ROOT / "content"
    if content.exists():
        shutil.rmtree(content)
    content.mkdir()
    for path, text in pages.items():
        (content / path).write_text(text, encoding="utf-8")

    marks = ROOT / "static" / "marks"
    if marks.exists():
        shutil.rmtree(marks)
    marks.mkdir()
    for out_name, src in images.items():
        shutil.copyfile(src, marks / out_name)

    back = '<p class="lede"><a href="./">Back to the player\'s guide</a></p>'
    map_html = map_html.replace("</header>", f"  {back}\n  </header>", 1)
    (ROOT / "static" / "map.html").write_text(
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        + map_html.replace("<div class=\"wrap\">", "</head>\n<body>\n<div class=\"wrap\">", 1)
        + "\n</body>\n</html>\n",
        encoding="utf-8",
    )

    print(f"Synced {len(pages)} pages, {len(images)} clan marks and the map from {guide}")
    if extra:
        print("Not published (add them to ORDER in scripts/sync.py to include): " + ", ".join(extra))


def config_title():
    m = re.search(r'^title\s*=\s*"([^"]+)"', (ROOT / "config.toml").read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else "Player Guide"


if __name__ == "__main__":
    main()
