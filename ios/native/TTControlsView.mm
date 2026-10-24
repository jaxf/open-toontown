#import "TTControlsView.h"
#include <cmath>

@interface TTStickView : UIView
@property(nonatomic, copy) void (^changed)(CGFloat, CGFloat);
- (void)cancel;
@end

@implementation TTStickView {
    UITouch *_contact;
    UIView *_thumb;
}

- (instancetype)initWithFrame:(CGRect)frame {
    self = [super initWithFrame:frame];
    if (self) {
        self.multipleTouchEnabled = YES;
        self.backgroundColor = [UIColor colorWithWhite:0.08 alpha:0.32];
        self.layer.borderWidth = 2;
        self.layer.borderColor = [UIColor colorWithWhite:1 alpha:0.55].CGColor;
        _thumb = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 56, 56)];
        _thumb.backgroundColor = [UIColor colorWithWhite:1 alpha:0.7];
        _thumb.layer.cornerRadius = 28;
        _thumb.userInteractionEnabled = NO;
        [self addSubview:_thumb];
        self.accessibilityLabel = @"Movement joystick";
        self.accessibilityHint = @"Drag to walk or turn";
    }
    return self;
}

- (void)layoutSubviews {
    [super layoutSubviews];
    self.layer.cornerRadius = CGRectGetWidth(self.bounds) / 2;
    [self cancel]; // Resizing/rotation cannot leave a direction held.
}

- (void)updateContact {
    CGPoint p = [_contact locationInView:self];
    CGPoint center = CGPointMake(CGRectGetMidX(self.bounds), CGRectGetMidY(self.bounds));
    CGFloat radius = MAX(1, MIN(center.x, center.y) - 28);
    CGFloat x = (p.x - center.x) / radius;
    CGFloat y = (center.y - p.y) / radius;
    CGFloat length = std::hypot(x, y);
    if (length > 1) { x /= length; y /= length; }
    _thumb.center = CGPointMake(center.x + x * radius, center.y - y * radius);
    if (self.changed) self.changed(x, y);
}

- (void)touchesBegan:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event {
    if (!_contact) {
        _contact = touches.anyObject;
        [self updateContact];
    }
}

- (void)touchesMoved:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event {
    if (_contact && [touches containsObject:_contact]) [self updateContact];
}

- (void)touchesEnded:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event {
    if (_contact && [touches containsObject:_contact]) [self cancel];
}

- (void)touchesCancelled:(NSSet<UITouch *> *)touches withEvent:(UIEvent *)event {
    if (_contact && [touches containsObject:_contact]) [self cancel];
}

- (void)cancel {
    _contact = nil;
    _thumb.center = CGPointMake(CGRectGetMidX(self.bounds), CGRectGetMidY(self.bounds));
    if (self.changed) self.changed(0, 0);
}
@end

@implementation TTControlsView {
    TTStickView *_stick;
    UIButton *_jump;
    BOOL _jumpHeld;
}

- (instancetype)initWithFrame:(CGRect)frame {
    self = [super initWithFrame:frame];
    if (self) {
        self.backgroundColor = UIColor.clearColor;
        self.multipleTouchEnabled = YES;
        _gameplayEnabled = YES;
        _stick = [[TTStickView alloc] initWithFrame:CGRectZero];
        __weak TTControlsView *weakSelf = self;
        _stick.changed = ^(CGFloat x, CGFloat y) {
            TTControlsView *view = weakSelf;
            if (view) [view.delegate controlsView:view movedStickX:x y:y];
        };
        [self addSubview:_stick];
        _jump = [UIButton buttonWithType:UIButtonTypeSystem];
        [_jump setTitle:@"Jump" forState:UIControlStateNormal];
        [_jump setTitleColor:UIColor.whiteColor forState:UIControlStateNormal];
        _jump.titleLabel.font = [UIFont boldSystemFontOfSize:20];
        _jump.backgroundColor = [UIColor colorWithRed:0.12 green:0.40 blue:0.78 alpha:0.8];
        _jump.layer.cornerRadius = 40;
        _jump.accessibilityLabel = @"Jump";
        _jump.exclusiveTouch = NO;
        [_jump addTarget:self action:@selector(jumpDown:) forControlEvents:UIControlEventTouchDown];
        [_jump addTarget:self action:@selector(jumpUp:) forControlEvents:
            UIControlEventTouchUpInside | UIControlEventTouchUpOutside | UIControlEventTouchCancel];
        [self addSubview:_jump];
        _stick.translatesAutoresizingMaskIntoConstraints = NO;
        _jump.translatesAutoresizingMaskIntoConstraints = NO;
        UILayoutGuide *safe = self.safeAreaLayoutGuide;
        [NSLayoutConstraint activateConstraints:@[
            [_stick.leadingAnchor constraintEqualToAnchor:safe.leadingAnchor constant:24],
            [_stick.bottomAnchor constraintEqualToAnchor:safe.bottomAnchor constant:-20],
            [_stick.widthAnchor constraintEqualToConstant:148],
            [_stick.heightAnchor constraintEqualToAnchor:_stick.widthAnchor],
            [_jump.trailingAnchor constraintEqualToAnchor:safe.trailingAnchor constant:-28],
            [_jump.bottomAnchor constraintEqualToAnchor:safe.bottomAnchor constant:-32],
            [_jump.widthAnchor constraintEqualToConstant:80],
            [_jump.heightAnchor constraintEqualToAnchor:_jump.widthAnchor],
        ]];
        [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(appInactive:)
            name:UIApplicationWillResignActiveNotification object:nil];
    }
    return self;
}

- (UIView *)hitTest:(CGPoint)point withEvent:(UIEvent *)event {
    if (!self.gameplayEnabled) return nil;
    UIView *hit = [super hitTest:point withEvent:event];
    return hit == self ? nil : hit;
}

- (void)jumpDown:(id)sender {
    if (!_gameplayEnabled || _jumpHeld) return;
    _jumpHeld = YES;
    [self.delegate controlsView:self jumpPressed:YES];
}

- (void)jumpUp:(id)sender {
    if (!_jumpHeld) return;
    _jumpHeld = NO;
    [self.delegate controlsView:self jumpPressed:NO];
}

- (void)cancelAllTouches {
    [_stick cancel];
    [self jumpUp:nil];
    _jump.highlighted = NO;
}

- (void)setGameplayEnabled:(BOOL)enabled {
    [self cancelAllTouches];
    _gameplayEnabled = enabled;
    _stick.userInteractionEnabled = enabled;
    _jump.enabled = enabled;
    _stick.hidden = !enabled;
    _jump.hidden = !enabled;
}

- (void)appInactive:(NSNotification *)notification {
    [self cancelAllTouches];
}

- (void)willMoveToWindow:(UIWindow *)newWindow {
    [self cancelAllTouches];
    [super willMoveToWindow:newWindow];
}

- (void)dealloc {
    [[NSNotificationCenter defaultCenter] removeObserver:self];
}
@end
