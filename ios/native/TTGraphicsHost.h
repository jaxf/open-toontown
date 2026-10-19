#pragma once
#import <UIKit/UIKit.h>

NS_ASSUME_NONNULL_BEGIN

/// Main thread only, before ShowBase creates its window. The host owns the
/// container and places TTControlsView above it. Only one game window is allowed.
/// Load PRC BEFORE registration: window-type onscreen, load-display (empty),
/// aux-display (empty), threading-model (empty), sync-video false. Pipe selection
/// caches display settings on first access; loading them afterward is too late.
BOOL TTConfigureGraphicsHost(UIView *container);

/// Resume explicitly after the app becomes active; resignation suspends itself.
/// Also pause the display link and TTGameInputBridge when the app resigns active.
void TTSetGraphicsActive(BOOL active);

/// Call after removing all Panda windows, on the main thread in the foreground.
/// Returns NO while a window still owns the drawing surface.
BOOL TTClearGraphicsHost(void);

/// Link/registration entry point; does not open a window or create a GL context.
void TTRegisterGraphicsPipe(void);

NS_ASSUME_NONNULL_END
