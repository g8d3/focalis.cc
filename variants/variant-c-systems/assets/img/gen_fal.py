import os, sys, json, time, requests, pathlib

# Ensure FAL_KEY is set
key = os.environ.get("FAL_KEY", "")
if not key:
    print("ERROR: FAL_KEY not set", file=sys.stderr)
    sys.exit(1)
print(f"FAL_KEY len={len(key)} prefix={key[:8]}...")

import fal_client

base = "/home/vuos/code/p4/sites/focalis.cc/variants/variant-c-systems/assets/img"
os.makedirs(base, exist_ok=True)

prompts = {
    "hero": {
        "prompt": "minimal premium tech infrastructure isometric illustration, light background off-white #FAF9F7, floating translucent data pipeline nodes connected by thin teal lines, soft shadows, navy #0F2342 accents, clean enterprise SaaS hero, ultra sharp, 8k, no text, no people",
        "image_size": "landscape_16_9",
        "file": "hero.jpg"
    },
    "data-pipeline": {
        "prompt": "abstract data pipeline visualization, light stone background, flowing particle streams through geometric pipes, teal and navy, minimal, premium tech product image, no text",
        "image_size": "square_hd",
        "file": "data-pipeline.jpg"
    },
    "automation-suite": {
        "prompt": "workflow automation visual, interconnected workflow cards floating in light space, subtle glass morphism, teal connections, navy typography accents, premium enterprise software, no text, no people",
        "image_size": "square_hd",
        "file": "automation-suite.jpg"
    },
    "integration-layer": {
        "prompt": "API integration layer abstract, 40+ connector nodes as minimalist icons orbiting a central hub, light background, fine lines, navy and teal, clean, no text",
        "image_size": "square_hd",
        "file": "integration-layer.jpg"
    }
}

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        if update.logs:
            for log in update.logs:
                print(f"  [log] {log.get('message','') if isinstance(log, dict) else log}")

results = {}

for name, cfg in prompts.items():
    print(f"\n=== Generating {name} ===")
    print(f"Prompt: {cfg['prompt'][:80]}...")
    print(f"Size: {cfg['image_size']}")
    try:
        start = time.time()
        result = fal_client.subscribe(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": cfg["prompt"],
                "image_size": cfg["image_size"],
                "num_images": 1,
                "enable_safety_checker": True
            },
            with_logs=True,
            on_queue_update=on_queue_update
        )
        elapsed = time.time() - start
        print(f"Result in {elapsed:.1f}s: {json.dumps(result, indent=2)[:2000]}")
        images = result.get("images") or result.get("data", {}).get("images") or []
        # handle different response shapes
        if not images and "images" in str(result):
            # try deeper
            pass
        if images:
            url = images[0]["url"]
            print(f"Image URL: {url}")
            # download
            out_path = os.path.join(base, cfg["file"])
            print(f"Downloading to {out_path} ...")
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(r.content)
            print(f"Saved {out_path} ({len(r.content)} bytes)")
            results[name] = {"url": url, "file": cfg["file"], "size": len(r.content), "elapsed": elapsed, "prompt": cfg["prompt"], "image_size": cfg["image_size"]}
        else:
            print(f"WARNING: No images in result for {name}: {result}")
            results[name] = {"error": "no images", "raw": result}
    except Exception as e:
        print(f"ERROR generating {name}: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        results[name] = {"error": str(e), "prompt": cfg["prompt"]}

# Write intermediate results
with open("/tmp/fal_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\n=== All done ===")
print(json.dumps(results, indent=2))
