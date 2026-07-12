# Live Website Publishing

The experiment publishes to a separate page in the personal website repository:

- Public URL: <https://www.aenguslynch.com/cultural-selection/>
- Website repository: `/home/aenguslynch/projects/aengusl.github.io`
- Website folder: `cultural-selection/`
- Existing Messiah Bench pages are not modified.

## Source files

- `publish_website.py` reads the canonical run state and decisions.
- `website_template.html` defines the editorial page design.
- `publish_loop.sh` republishes and pushes approximately every ten turns and once at completion.

The publisher copies only the current canonical artwork for each living religion. It also publishes aggregate state, the influence ranking, public history, and selected excerpts from agent reasoning.

## Manual publish

```bash
cd /home/aenguslynch/projects/aengusl.github.io
git pull --rebase origin main

cd /home/aenguslynch/projects/messiah-bench
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  experiments/2026-07-12-minimal-cultural-selection/publish_website.py

cd /home/aenguslynch/projects/aengusl.github.io
git add cultural-selection
git commit -m "Update cultural selection live page"
git push origin main
```

## Verification

Serve the website repository locally and inspect the new page:

```bash
cd /home/aenguslynch/projects/aengusl.github.io
python3 -m http.server 8765
```

Then open <http://127.0.0.1:8765/cultural-selection/>.
