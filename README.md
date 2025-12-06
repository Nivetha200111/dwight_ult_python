# Dwight Ultra — Web + Python

Browser-friendly port of the Dwight V13 evac sim with fixed POV lighting. The original pygame prototype (`dwight_ultra.py`) is still here, but you can now run everything in a canvas-based frontend that deploys as a static site.

## Run the web sim locally

1) Open `index.html` directly in a browser _or_ serve the folder for clean CORS behavior:
```bash
npx serve .
```
2) Use the controls listed in the sidebar (WASD/scroll/click/B/E/F/Space/R).

## Deploy to Vercel (zero config)

- The repo root now contains `index.html`, `style.css`, and `main.js`, so you can deploy straight from here:
```bash
vercel --prod
```
- Vercel will treat the project as a static site; no build step required.

## What’s included

- Canvas rendering of the isometric grid, rubble, exits, and hazard spread.
- Camera panning/zoom, person selection with dynamic lighting mask, and thought bubbles.
- Bomb/quake/fire events, stun + health logic, and pathfinding toward exits.
- Lightweight UI (stats + controls) styled for a single-page deploy.
