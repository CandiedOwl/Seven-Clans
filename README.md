# The Seven Clans

The player's guide to a dark-ages, shamanistic campaign, built with [Zola](https://www.getzola.org/) and published on GitHub Pages.

Everything in `content/` and `static/map.html` is generated from the Player Guide folder of the campaign's Obsidian vault. Don't edit them here; edit the vault and sync.

## Updating the site

1. Edit the notes in the vault's `Player Guide/` folder.
2. From this folder, run:

   ```sh
   python3 scripts/sync.py
   ```

   By default it reads the vault at `../Ancient-Darkness/Ancient Darkness`. Pass another path to use a different location.

3. Preview locally with `zola serve`, then open http://127.0.0.1:1111.
4. Commit and push. GitHub Actions builds the site and publishes it.

## The safety check

`scripts/sync.py` only copies notes from the Player Guide folder, plus the saved player map. It stops without writing anything if a note contains a word from its spoiler list, or links to a note outside the Player Guide. If it stops, fix the note in the vault and run it again.

To publish a new Player Guide note, add its name to `ORDER` in `scripts/sync.py`.
