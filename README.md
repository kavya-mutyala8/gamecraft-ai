README.md
Video link: https://youtu.be/GrftLZ6iHag





GameCraft AI 
GameCraft AI
An AI-powered game asset generator that turns one game idea into a cohesive set of game assets.
The Problem
Indie developers, game jams, and hobbyist creators need many visual assets (characters, environments, weapons, inventory icons) that look like they belong to the same game. AI image generators usually produce random, unrelated images. Each image drifts in style, palette, and perspective, so creators spend hours fixing or redrawing assets by hand.
Our Solution
Describe a game in one sentence, such as "a fantasy game set in an enchanted forest." GameCraft AI generates an art bible for the game and then produces a matching asset set: an entire colour palette. Every asset is generated from the same art bible, so the set reads as one visual world.
What It Does
- Art bible: an editable art direction covering palette, rendering, lighting, camera, materials, and a list of things to avoid. Every asset is generated from it.
- Asset set: a character, an environment, a weapon, and two inventory icons, shown in a grid.
- Regenerate: redo any single asset without changing the others.
- Export: a ZIP of the approved assets plus a manifest.json that records the concept, the art bible, and each exported file.
How It Works (Demo Flow)
1. Enter a game concept.
2. Review the art bible and edit a line, such as the palette.
3. See the asset grid fill in with a character, an environment, weapons, and icons.
4. Regenerate an asset that doesn't fit.
5. Export the ZIP and open manifest.json.
Technology
- Backend: Python with FastAPI. Endpoints create a project, edit the art bible, regenerate an asset, and export the ZIP and manifest.
- Frontend: a single-page interface in HTML, CSS, and JavaScript for the concept form, the before/after comparison, the art bible editor, the asset grid, and export.
- Image generation: an image model, with the same art bible text used across the set. Icons and weapons were generated with a character image as a visual reference.
Challenges
Frontend ↔ backend integration (first time): Our request formats didn't match, so I mapped them with an adapter in the code.
Backend bug: A backend bug (the response was built before the database filled in dates) crashed generation, and the browser reported it as "can't reach the backend" — which sent me debugging the wrong thing.
Image model providers: Hugging Face and Gemini image models turned out to be paid, so I found Cloudflare Workers AI (free) and wrote the provider code for it.
Git: Merging teammates' changes, the Vim commit screen, and keeping API keys out of the repo.
Time: Building, testing, and integrating everything in under 3 days.
Accomplishments
- A full path from one concept sentence to an exported ZIP with a manifest.
- Five generated assets that share one palette, outline style, and light direction.
What's Next
- Live image generation from any concept, wired to an image provider
- Multiple styles per project and shareable style libraries
- Background removal and sprite-sheet export
- Unity and Godot plugins
Why It Matters
Style consistency is the difference between an AI image toy and a practical production tool. GameCraft AI helps more people turn ideas into playable worlds, and shows how generative AI can support creative work rather than replace it.
GitHub Repository
https://github.com/kavya-mutyala8/gamecraft-ai



