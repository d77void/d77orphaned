# D77orphaned: wasp renders through scenefx, which needs EGL/GLES and, unlike
# plain wlroots, refuses to start on software rendering (llvmpipe) unless this
# is set — so without a usable GPU (VMs, odd hardware, nomodeset) the wasp
# session died at once ("Software rendering detected ... couldn't create
# renderer"). With a GPU, hardware rendering is still used.
export WLR_RENDERER_ALLOW_SOFTWARE=1
