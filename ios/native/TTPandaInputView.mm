#import "TTPandaInputView.h"
#include "graphicsWindowInputDevice.h"
#include "mouseButton.h"
#include <cmath>

@implementation TTPandaInputView {
    PT(GraphicsWindowInputDevice) _device;
    UITouch *_pointerTouch;
    BOOL _pressed;
}

- (instancetype)initWithFrame:(CGRect)frame {
    self = [super initWithFrame:frame];
    if (self) {
        self.multipleTouchEnabled = YES;
        _inputEnabled = NO;
        [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(appInactive:)
            name:UIApplicationWillResignActiveNotification object:nil];
    }
    return self;
}

- (void)attachInputDevice:(GraphicsWindowInputDevice *)device {
    NSAssert(NSThread.isMainThread, @"Panda input belongs to the engine/UI thread");
    [self cancelPointer];
    _device = device;
}

- (void)setDrawableSize:(CGSize)size {
    [self cancelPointer];
    _drawableSize = size;
}

- (void)setInputEnabled:(BOOL)enabled {
    [self cancelPointer];
    _inputEnabled = enabled;
}

- (BOOL)canAcceptPointer {
    return _inputEnabled && _device != nullptr &&
        std::isfinite(_drawableSize.width) && std::isfinite(_drawableSize.height) &&
        _drawableSize.width > 0 && _drawableSize.height > 0 &&
        self.bounds.size.width > 0 && self.bounds.size.height > 0;
}

- (void)updatePointer:(UITouch *)touch {
    CGPoint point = [touch locationInView:self];
    if (!CGRectContainsPoint(self.bounds, point)) {
        _device->set_pointer_out_of_window();
        return;
    }
    // Panda expects top-left pixel coordinates, not UIKit logical points or
    // safe-area-relative coordinates. Scale using the actual drawable size.
    double x = (point.x - self.bounds.origin.x) * _drawableSize.width / self.bounds.size.width;
    double y = (point.y - self.bounds.origin.y) * _drawableSize.height / self.bounds.size.height;
    _device->set_pointer_in_window(x, y);
}

- (void)touchesBegan:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event {
    if (_pointerTouch || ![self canAcceptPointer]) return;
    // Never turn secondary fingers into right/middle clicks. UIKit retains
    // each contact's target, so movement/jump touches stay with the overlay.
    _pointerTouch = touches.anyObject;
    if (!_pointerTouch) return;
    [self updatePointer:_pointerTouch];
    _device->button_down(MouseButton::one());
    _pressed = YES;
}

- (void)touchesMoved:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event {
    if (_pointerTouch && [touches containsObject:_pointerTouch] && [self canAcceptPointer])
        [self updatePointer:_pointerTouch];
}

- (void)touchesEnded:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event {
    if (!_pointerTouch || ![touches containsObject:_pointerTouch]) return;
    if ([self canAcceptPointer]) [self updatePointer:_pointerTouch];
    if (_pressed && _device != nullptr) _device->button_up(MouseButton::one());
    _pressed = NO;
    _pointerTouch = nil;
    // Preserve the release position until Panda processes the click. Clearing
    // it here can make a complete tap between frames miss DirectGUI regions.
}

- (void)touchesCancelled:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event {
    if (_pointerTouch && [touches containsObject:_pointerTouch]) [self cancelPointer];
}

- (void)cancelPointer {
    if (_device != nullptr) {
        // Cancellation/resize/background must not activate a hovered button.
        _device->set_pointer_out_of_window();
        if (_pressed) _device->button_up(MouseButton::one());
    }
    _pressed = NO;
    _pointerTouch = nil;
}

- (void)appInactive:(NSNotification *)notification {
    self.inputEnabled = NO; // The app host explicitly re-enables on resume.
}

- (void)willMoveToWindow:(UIWindow *)newWindow {
    [self cancelPointer];
    [super willMoveToWindow:newWindow];
}

- (void)dealloc {
    [self cancelPointer];
    [[NSNotificationCenter defaultCenter] removeObserver:self];
}
@end
