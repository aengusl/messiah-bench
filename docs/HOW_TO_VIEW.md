# How to View Simulation Dashboards and Sacrament Gallery

## Quick Start: Local HTTP Server

Start an HTTP server from the messiah-bench directory:

```bash
cd /home/aenguslynch/projects/messiah-bench
python -m http.server 8000
```

Then open your browser to:

- **V1 Dashboard:** `http://localhost:8000/runs/v1/index.html`
- **V2 Dashboard:** `http://localhost:8000/runs/v2/index.html`
- **Sacrament Gallery:** `http://localhost:8000/gallery.html`

## Key URLs

| Content | URL |
|---------|-----|
| V1 Simulation Dashboard | `http://localhost:8000/runs/v1/index.html` |
| V2 Simulation Dashboard | `http://localhost:8000/runs/v2/index.html` |
| Sacrament Gallery (Main) | `http://localhost:8000/gallery.html` |
| Simulation Data (V1) | `http://localhost:8000/runs/v1/world_state.json` |
| Simulation Data (V2) | `http://localhost:8000/runs/v2/world_state.json` |

## Remote Access via SSH Port Forwarding

If you're connecting from a remote machine (e.g., over SSH), forward the port:

```bash
ssh -L 8000:localhost:8000 aenguslynch@<server-ip>
```

Then access the same local URLs in your browser (`http://localhost:8000/...`).

## Copy Files to Local Machine

To download and view files locally:

```bash
# Copy a single sacrament
scp aenguslynch@<server-ip>:/home/aenguslynch/projects/messiah-bench/runs/v1/sacraments/<filename>.html ./

# Copy entire V1 run
scp -r aenguslynch@<server-ip>:/home/aenguslynch/projects/messiah-bench/runs/v1 ./

# Copy gallery and main files
scp aenguslynch@<server-ip>:/home/aenguslynch/projects/messiah-bench/gallery.html ./
scp aenguslynch@<server-ip>:/home/aenguslynch/projects/messiah-bench/religion_and_the_machine.html ./
```

Then serve locally on your machine:

```bash
python -m http.server 8000
```

## Important Note: Gallery Requires HTTP Server

The **Sacrament Gallery** (`gallery.html`) must be served over HTTP — it cannot be opened directly as a file (`file://`). This is because:

1. The gallery fetches simulation data from `world_state.json` dynamically
2. Browser security policies block local file requests from HTML documents
3. An HTTP server (even localhost) bypasses this restriction

If you copy the gallery to your local machine, you must also include the corresponding `world_state.json` file and serve both over HTTP.

## Server Options

### Python Built-in (Recommended for Quick Setup)

```bash
python -m http.server 8000
```

### Python with Live Reload (Better for Development)

```bash
pip install http-server
http-server -p 8000
```

### Node.js (if available)

```bash
npx http-server -p 8000
```

## Troubleshooting

- **Port already in use:** Change to a different port: `python -m http.server 8080`
- **Gallery shows blank:** Ensure `world_state.json` is in the correct directory and the server is running
- **Files not loading:** Check that you're using `http://` not `file://`
