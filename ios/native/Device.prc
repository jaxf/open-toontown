# Loaded before native pipe registration, then again after game defaults.
# The iOS engine overlay supports registered pipes without dynamic plugins.
load-display static TTGraphicsPipe
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
# Match the bundled payload, including DirectGUI's engine fallback models.
model-path engine-models
verify-ssl true
ca-bundle-filename ../python/site-packages/certifi/cacert.pem
require-window true
icon-filename
cursor-filename
# The host registers the linked OpenAL factory. Audio-session interruption
# handling and actual device playback still require integration/testing.
audio-library-name p3openal_audio
