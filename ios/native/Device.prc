# Loaded before native pipe registration, then again after game defaults.
load-display
aux-display
window-type onscreen
threading-model
sync-video false
aspect-ratio 0
depth-bits 24
stencil-bits 8
framebuffer-multisample false
multisamples 0
framebuffer-srgb false
mobile-client true
toontown-auto-run false
# The static OpenAL factory and iOS audio session still need integration.
# Keep the actual requested audio backend; never substitute silent audio to
# declare the full game complete.
audio-library-name p3openal_audio
