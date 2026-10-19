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
# The host registers the linked OpenAL factory. Audio-session interruption
# handling and actual device playback still require integration/testing.
audio-library-name p3openal_audio
