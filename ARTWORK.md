# Artwork and provenance

The wallpaper is an AI-generated illustrated interpretation of the owner's
photograph taken in Japan: an old pine with timber supports beside water.
Its composition and High Fidelity treatment were reviewed and approved by the
owner during development of this personal theme.

- Original input to the upscaler: `assets/perch-current-source.png`, 1672 × 941.
- Original SHA-256: `be169625e5019ebed92e78bd9545c3fb844333aae5acb7158e82fa30269126d1`.
- Upscaler: Upscayl 2.15.0, bundled NCNN/Vulkan engine, `high-fidelity-4x` model.
- Intermediate resolution: 6688 × 3764.
- Included wallpaper: `theme/backgrounds/00-perch-current-ai-5k.png`, 5120 × 2880.
- Final processing: Pillow Lanczos downsampling with a minimal centered aspect
  ratio crop; no additional sharpening or color grading.

This is AI super-resolution, not native 5K source detail. The final wallpaper is
included so another machine needs neither Upscayl nor the intermediate master.
`tools/upscale.sh` documents the optional regeneration procedure.

The perch emblem is an original single-color vector mark made for this theme.
No third-party reference photographs, stock wallpaper art, model weights, or
upscaler binaries are included in the repository.
