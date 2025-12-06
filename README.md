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

If you prefer a quick local preview:
```bash
python -m http.server 8000
```
then open http://localhost:8000.

## What’s included

- Full-screen **top-down** canvas rendering of the grid, rubble, exits, and hazard spread (no isometric tilt).
- Workers idle until you trigger a disaster (Bomb/Quake/Fire); then they evacuate toward exits.
- Camera pan/zoom, person selection with POV light mask, and thought bubbles.
- Bomb/quake/fire events, stun + health logic, and pathfinding toward exits.
- Fire now has intensity, spread/decay, smoke and heat; smoke reduces visibility and speed, heat damages and reroutes evac paths.
- Scenario gallery (electrical/chemical/kitchen) with auto-seeded ignitions, wind, and timed suppression bursts.
- React overlay HUD (CDN React 18 + htm) with quick action buttons, toggles for heatmap/sensors/guidance, scenario selector, metrics (evac time, congestion).
- IoT-style sensor nodes (auto-placed or shift-click to place) with live trigger state and coverage rings; mock WebSocket feed simulates sensor updates.
- Optional TF.js spread predictor (CDN) adjusts fire propagation based on heat/smoke/occupancy/wind for a “smart safety” angle.
- Targeted disasters: right-click (or ctrl+click) to place fire/bomb/quake at the cursor; choose mode with keys 1 (fire), 2 (bomb), 3 (quake). Random disaster with T. 
- Sounds: alarm on evac, crackling fire loop while hazards burn, bomb/quake one-shots (muted if Howler.js unavailable).
