# FAL Media Manifest — variant-c-systems (light theme)

Generated via `fal_client` + `fal-ai/flux/schnell` on 2026-03-31.

## Model
- **Model:** `fal-ai/flux/schnell` (fast)
- **Client:** `fal_client==1.0.1` (Python)
- **Auth:** `$FAL_KEY` (69 chars, prefix `eef41d37…`)
- **Safety checker:** enabled (`enable_safety_checker: true`)

## Palette & Intent
Light theme, premium tech studio, Focalis Systems variant C — navy `#0F2342` + teal `#14B8A6` + stone/off-white `#FAF9F7`, glass morphism, soft shadows, no text, no people, enterprise SaaS.

## Images

| File | Prompt | Size | Seed | Remote URL (fal.media, expires) | Local | Dimensions | Bytes |
|------|--------|------|------|----------------------------------|-------|------------|-------|
| `hero.jpg` | `minimal premium tech infrastructure isometric illustration, light background off-white #FAF9F7, floating translucent data pipeline nodes connected by thin teal lines, soft shadows, navy #0F2342 accents, clean enterprise SaaS hero, ultra sharp, 8k, no text, no people` | `landscape_16_9` | `1906783749` | `https://v3b.fal.media/files/b/0aa88093/6xoJ14QlttpqM0UL0fWtR.jpg` | `assets/img/hero.jpg` | 1024×576 | 193670 |
| `data-pipeline.jpg` | `abstract data pipeline visualization, light stone background, flowing particle streams through geometric pipes, teal and navy, minimal, premium tech product image, no text` | `square_hd` | `2071415139` | `https://v3b.fal.media/files/b/0aa88094/AS6ALp7ZCV9iLUQlNKbgv.jpg` | `assets/img/data-pipeline.jpg` | 1024×1024 | 723548 |
| `automation-suite.jpg` | `workflow automation visual, interconnected workflow cards floating in light space, subtle glass morphism, teal connections, navy typography accents, premium enterprise software, no text, no people` | `square_hd` | `1302736129` | `https://v3b.fal.media/files/b/0aa88094/383fL-oVzTOXHWUlYmXaF.jpg` | `assets/img/automation-suite.jpg` | 1024×1024 | 422936 |
| `integration-layer.jpg` | `API integration layer abstract, 40+ connector nodes as minimalist icons orbiting a central hub, light background, fine lines, navy and teal, clean, no text` | `square_hd` | `1272157089` | `https://v3b.fal.media/files/b/0aa88094/vvfuCuxSOuHX6ovsrsFPy.jpg` | `assets/img/integration-layer.jpg` | 1024×1024 | 713535 |

## Generation log

All 4 images completed in ~10.1s total (2.3–2.9s each, inference 0.8–1.25s). Saved via `requests.get(url)` -> `assets/img/<file>.jpg`. Logs captured from `on_queue_update`. No NSFW flags (`has_nsfw_concepts: [false]`).

Reproduce:
```python
import fal_client
def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        print(update.logs)
result = fal_client.subscribe("fal-ai/flux/schnell", arguments={
  "prompt": "minimal premium tech infrastructure isometric illustration, light background off-white #FAF9F7, floating translucent data pipeline nodes connected by thin teal lines, soft shadows, navy #0F2342 accents, clean enterprise SaaS hero, ultra sharp, 8k, no text, no people",
  "image_size": "landscape_16_9", "num_images": 1, "enable_safety_checker": True
}, with_logs=True, on_queue_update=on_queue_update)
print(result["images"][0]["url"])  # -> curl -o hero.jpg <url>
```

## How to use in HTML (relative paths)

Variant root: `variants/variant-c-systems/`

```html
<!-- Hero (if adding a hero image block) -->
<img src="assets/img/hero.jpg" alt="Focalis infrastructure hero — translucent data pipeline, light theme" width="1024" height="576" loading="eager" fetchpriority="high">

<!-- Video poster -->
<video poster="assets/img/hero.jpg" ...><source src="assets/video/hero.mp4" type="video/mp4"></video>

<!-- Products -->
<img src="assets/img/data-pipeline.jpg" alt="Data Pipeline — abstract pipeline visualization" width="1024" height="1024" loading="lazy">
<img src="assets/img/automation-suite.jpg" alt="Automation Suite — workflow cards, glass morphism" width="1024" height="1024" loading="lazy">
<img src="assets/img/integration-layer.jpg" alt="Integration Layer — connector nodes orbiting hub" width="1024" height="1024" loading="lazy">
```

Current `index.html` has been updated to:
- `poster="assets/img/hero.jpg"` (was unsplash)
- product card images replaced with `assets/img/data-pipeline.jpg`, `assets/img/automation-suite.jpg`, `assets/img/integration-layer.jpg`
- video `source` keeps `cdn.coverr.co` fallback until `assets/video/hero.mp4` is generated (see `assets/video/PLACEHOLDER.md`)

## Video
- Attempted: `fal-ai/fast-svd` + `fal-ai/kling-video` with prompt `slow smooth camera orbit around minimal tech infrastructure, light background, particles flowing, 5 seconds, premium`
- Result: queue >120s, skipped. Placeholder note at `assets/video/PLACEHOLDER.md`. CSS `.video-fallback` is active so UI is not broken.
- To add later: generate mp4 → `assets/video/hero.mp4` → update `<source src="assets/video/hero.mp4">`

## 3D
- Skipped per priority (images first). Placeholders at `assets/3d/PLACEHOLDER.md`. Candidates: `fal-ai/trellis`, `fal-ai/hunyuan3d-v2` → `assets/3d/*.glb`.

## Files on disk
```
assets/img/hero.jpg                 190 KB  1024×576
assets/img/data-pipeline.jpg        707 KB  1024×1024
assets/img/automation-suite.jpg     414 KB  1024×1024
assets/img/integration-layer.jpg    697 KB  1024×1024
assets/img/MANIFEST.md              (this file)
assets/video/PLACEHOLDER.md
assets/3d/PLACEHOLDER.md
```

Regenerate: `FAL_KEY=$FAL_KEY python3 /tmp/gen_fal.py` (see `/tmp/gen_fal.py` and `/tmp/fal_results.json` on this machine).

— FAL MEDIA GENERATOR, focalis.cc variant-c-systems
