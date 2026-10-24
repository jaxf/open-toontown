#pragma once
#import "TTPandaInputView.h"
#import <OpenGLES/EAGL.h>
#import <OpenGLES/ES2/gl.h>

NS_ASSUME_NONNULL_BEGIN

/// Device drawable. All GL calls belong to the main engine/UI thread.
@interface TTGLESView : TTPandaInputView
@property(nonatomic, readonly) EAGLContext *context;
@property(nonatomic, readonly) GLuint framebuffer;
@property(nonatomic, getter=isRenderingEnabled) BOOL renderingEnabled;
/// Creates/reallocates only when needed. Preserves the previous FBO binding so
/// Panda's state cache remains correct. Returns NO while inactive/unattached.
- (BOOL)prepareDrawable;
- (BOOL)makeCurrent;
- (BOOL)presentDrawable;
/// Explicit foreground teardown after Panda releases its state guardian.
- (void)destroyDrawable;
@end

NS_ASSUME_NONNULL_END
