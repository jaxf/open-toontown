#import "TTGLESView.h"
#import <QuartzCore/CAEAGLLayer.h>
#include <cmath>

@implementation TTGLESView {
    GLuint _colorBuffer;
    GLuint _depthBuffer;
    BOOL _needsStorage;
}

+ (Class)layerClass { return CAEAGLLayer.class; }

- (instancetype)initWithFrame:(CGRect)frame {
    self = [super initWithFrame:frame];
    if (self) {
        _context = [[EAGLContext alloc] initWithAPI:kEAGLRenderingAPIOpenGLES2];
        if (!_context) return nil;
        self.opaque = YES;
        self.contentScaleFactor = UIScreen.mainScreen.scale;
        CAEAGLLayer *layer = (CAEAGLLayer *)self.layer;
        layer.opaque = YES;
        layer.drawableProperties = @{kEAGLDrawablePropertyRetainedBacking: @NO,
                                     kEAGLDrawablePropertyColorFormat: kEAGLColorFormatRGBA8};
        _needsStorage = YES;
        [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(suspendRendering:)
            name:UIApplicationWillResignActiveNotification object:nil];
    }
    return self;
}

- (void)layoutSubviews {
    [super layoutSubviews];
    _needsStorage = YES;
    self.drawableSize = CGSizeZero; // No stale touch coordinates during rotation.
}

- (void)didMoveToWindow {
    [super didMoveToWindow];
    if (self.window) self.contentScaleFactor = self.window.screen.scale;
    _needsStorage = YES;
    self.drawableSize = CGSizeZero;
}

- (BOOL)makeCurrent {
    if (!NSThread.isMainThread || !_context ||
        UIApplication.sharedApplication.applicationState == UIApplicationStateBackground) return NO;
    return [EAGLContext setCurrentContext:_context];
}

- (void)setRenderingEnabled:(BOOL)enabled {
    NSAssert(NSThread.isMainThread, @"Rendering belongs to the main thread");
    if (!enabled) {
        self.inputEnabled = NO;
        // WillResignActive arrives before backgrounding. Finish queued GPU work
        // here; no GL work is submitted from a background notification.
        if (_renderingEnabled && [self makeCurrent]) glFinish();
    }
    _renderingEnabled = enabled;
}

- (void)suspendRendering:(NSNotification *)notification {
    self.renderingEnabled = NO;
}

- (BOOL)prepareDrawable {
    if (!NSThread.isMainThread || !_renderingEnabled || !self.window ||
        UIApplication.sharedApplication.applicationState != UIApplicationStateActive) return NO;
    CGSize points = self.bounds.size;
    if (!std::isfinite(points.width) || !std::isfinite(points.height) ||
        points.width <= 0 || points.height <= 0 || ![self makeCurrent]) return NO;
    if (!_needsStorage) return YES;

    GLint previousFBO = 0, previousRBO = 0;
    glGetIntegerv(GL_FRAMEBUFFER_BINDING, &previousFBO);
    glGetIntegerv(GL_RENDERBUFFER_BINDING, &previousRBO);
    if (!_framebuffer) glGenFramebuffers(1, &_framebuffer);
    if (!_colorBuffer) glGenRenderbuffers(1, &_colorBuffer);
    if (!_depthBuffer) glGenRenderbuffers(1, &_depthBuffer);
    glBindFramebuffer(GL_FRAMEBUFFER, _framebuffer);
    glBindRenderbuffer(GL_RENDERBUFFER, _colorBuffer);
    BOOL ready = [_context renderbufferStorage:GL_RENDERBUFFER fromDrawable:(CAEAGLLayer *)self.layer];
    GLint width = 0, height = 0;
    if (ready) {
        glGetRenderbufferParameteriv(GL_RENDERBUFFER, GL_RENDERBUFFER_WIDTH, &width);
        glGetRenderbufferParameteriv(GL_RENDERBUFFER, GL_RENDERBUFFER_HEIGHT, &height);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, _colorBuffer);
        glBindRenderbuffer(GL_RENDERBUFFER, _depthBuffer);
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT16, width, height);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, _depthBuffer);
        ready = width > 0 && height > 0 &&
            glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE;
    }
    glBindFramebuffer(GL_FRAMEBUFFER, previousFBO);
    glBindRenderbuffer(GL_RENDERBUFFER, previousRBO);
    if (!ready) return NO;
    self.drawableSize = CGSizeMake(width, height);
    _needsStorage = NO;
    return YES;
}

- (BOOL)presentDrawable {
    if (!_renderingEnabled || _needsStorage ||
        UIApplication.sharedApplication.applicationState != UIApplicationStateActive || ![self makeCurrent]) return NO;
    GLint previous = 0;
    glGetIntegerv(GL_RENDERBUFFER_BINDING, &previous);
    glBindRenderbuffer(GL_RENDERBUFFER, _colorBuffer);
    BOOL result = [_context presentRenderbuffer:GL_RENDERBUFFER];
    glBindRenderbuffer(GL_RENDERBUFFER, previous);
    if (!result) {
        _needsStorage = YES;
        self.drawableSize = CGSizeZero;
    }
    return result;
}

- (void)destroyDrawable {
    self.renderingEnabled = NO;
    [self attachInputDevice:nullptr];
    if ([self makeCurrent]) {
        if (_framebuffer) glDeleteFramebuffers(1, &_framebuffer);
        if (_colorBuffer) glDeleteRenderbuffers(1, &_colorBuffer);
        if (_depthBuffer) glDeleteRenderbuffers(1, &_depthBuffer);
        [EAGLContext setCurrentContext:nil];
    }
    _framebuffer = _colorBuffer = _depthBuffer = 0;
    self.drawableSize = CGSizeZero;
    _needsStorage = YES;
}
@end
