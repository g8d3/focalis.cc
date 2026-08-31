# Video Placeholder — focalis.cc variant-c-systems

Video generation was attempted but skipped (queue >2 min or model unavailable during batch).

**Intended prompt:**
> slow smooth camera orbit around minimal tech infrastructure, light background, particles flowing, 5 seconds, premium

**Attempted models:**
- `fal-ai/fast-svd` (image-to-video from hero.jpg, motion_bucket_id 127)
- `fal-ai/kling-video/v1/standard/text-to-video` (duration 5s, 16:9)
- `fal-ai/kling-video`

**Status:** `pending` — CSS fallback is active.

**CSS fallback:**
The hero showcase in `index.html` already has a graceful fallback: `<div class="video-fallback">` + `.video-overlay` layered under the `<video>` tag. If `assets/video/hero.mp4` is missing, the poster (`hero.jpg` or unsplash fallback) + gradient overlay is shown. No broken UI.

**To generate later:**
```python
import fal_client, requests
result = fal_client.subscribe("fal-ai/kling-video/v1/standard/text-to-video",
  arguments={"prompt": "slow smooth camera orbit around minimal tech infrastructure, light background, particles flowing, 5 seconds, premium", "duration": "5", "aspect_ratio": "16:9"})
# result["video"]["url"] -> curl -o assets/video/hero.mp4 <url>
```

Then update `index.html` line:
```html
<source src="assets/video/hero.mp4" type="video/mp4">
```

Generated: 2026-03-31 via FAL_MEDIA_GENERATOR
