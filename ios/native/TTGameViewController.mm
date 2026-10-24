#import "TTGameViewController.h"
#import "TTEmbeddedRuntime.h"
#import "TTGraphicsHost.h"
#import "TTGameInputBridge.h"
#import <QuartzCore/CADisplayLink.h>
#import <AVFAudio/AVAudioSession.h>
#include <arpa/inet.h>

@interface TTGameViewController ()
- (void)frame:(CADisplayLink *)link;
@end

// CADisplayLink retains its target. A weak proxy avoids a controller/link cycle.
@interface TTFrameTarget : NSObject
@property(nonatomic, weak) TTGameViewController *owner;
- (void)tick:(CADisplayLink *)link;
@end
@implementation TTFrameTarget
- (void)tick:(CADisplayLink *)link { [self.owner frame:link]; }
@end

static BOOL TTValidServer(NSString *server) {
    if (!server.length) return NO;
    struct in_addr address;
    if (inet_pton(AF_INET, server.UTF8String, &address) != 1) return NO;
    uint32_t ip = ntohl(address.s_addr);
    return (ip >> 24) == 10 || (ip >> 24) == 127 || (ip >> 20) == 0xac1 ||
           (ip >> 16) == 0xc0a8 || (ip >> 22) == 0x191;
}

@implementation TTGameViewController {
    UIView *_gameContainer;
    UIScrollView *_form;
    UITextField *_server;
    UITextField *_token;
    UIButton *_connect;
    UILabel *_status;
    UIButton *_copyDiagnostic;
    TTControlsView *_controls;
    TTGameInputBridge *_input;
    TTEmbeddedRuntime *_runtime;
    CADisplayLink *_displayLink;
    BOOL _starting;
    BOOL _running;
    BOOL _active;
    BOOL _movementEnabled;
    BOOL _inFrame;
    BOOL _cleanupPending;
    NSError *_pendingError;
}

- (void)viewDidLoad {
    [super viewDidLoad];
    self.view.backgroundColor = UIColor.blackColor;
    _gameContainer = [[UIView alloc] initWithFrame:self.view.bounds];
    _gameContainer.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
    [self.view addSubview:_gameContainer];
    _controls = [[TTControlsView alloc] initWithFrame:self.view.bounds];
    _controls.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
    _controls.gameplayEnabled = NO;
    _controls.hidden = YES;
    [self.view addSubview:_controls];

    _form = [[UIScrollView alloc] init];
    _form.translatesAutoresizingMaskIntoConstraints = NO;
    _form.backgroundColor = UIColor.systemBackgroundColor;
    _form.keyboardDismissMode = UIScrollViewKeyboardDismissModeOnDrag;
    [self.view addSubview:_form];
    UILabel *title = [[UILabel alloc] init];
    title.text = @"Open Toontown";
    title.font = [UIFont preferredFontForTextStyle:UIFontTextStyleTitle2];
    _server = [[UITextField alloc] init];
    _server.placeholder = @"Private server address";
    _server.accessibilityLabel = @"Private server IPv4 address";
    _server.text = [[NSUserDefaults standardUserDefaults] stringForKey:@"privateServer"];
    _token = [[UITextField alloc] init];
    _token.placeholder = @"Player token";
    _token.accessibilityLabel = @"Player invitation token";
    _token.secureTextEntry = YES;
    for (UITextField *field in @[_server, _token]) {
        field.borderStyle = UITextBorderStyleRoundedRect;
        field.autocorrectionType = UITextAutocorrectionTypeNo;
        field.autocapitalizationType = UITextAutocapitalizationTypeNone;
        field.keyboardType = UIKeyboardTypeASCIICapable;
        field.spellCheckingType = UITextSpellCheckingTypeNo;
    }
    _connect = [UIButton buttonWithType:UIButtonTypeSystem];
    [_connect setTitle:@"Connect" forState:UIControlStateNormal];
    [_connect addTarget:self action:@selector(connect) forControlEvents:UIControlEventTouchUpInside];
    _status = [[UILabel alloc] init];
    _status.numberOfLines = 0;
    _status.font = [UIFont preferredFontForTextStyle:UIFontTextStyleFootnote];
    _status.text = @"Connect this device to your private network before joining.";
    _copyDiagnostic = [UIButton buttonWithType:UIButtonTypeSystem];
    [_copyDiagnostic setTitle:@"Copy error details" forState:UIControlStateNormal];
    [_copyDiagnostic addTarget:self action:@selector(copyDiagnostic) forControlEvents:UIControlEventTouchUpInside];
    _copyDiagnostic.hidden = YES;
    UIStackView *stack = [[UIStackView alloc] initWithArrangedSubviews:@[title, _server, _token, _connect, _status, _copyDiagnostic]];
    stack.axis = UILayoutConstraintAxisVertical;
    stack.spacing = 12;
    stack.translatesAutoresizingMaskIntoConstraints = NO;
    [_form addSubview:stack];
    UILayoutGuide *safe = self.view.safeAreaLayoutGuide;
    [NSLayoutConstraint activateConstraints:@[
        [_form.leadingAnchor constraintEqualToAnchor:safe.leadingAnchor],
        [_form.trailingAnchor constraintEqualToAnchor:safe.trailingAnchor],
        [_form.topAnchor constraintEqualToAnchor:safe.topAnchor],
        [_form.bottomAnchor constraintEqualToAnchor:self.view.keyboardLayoutGuide.topAnchor],
        [stack.leadingAnchor constraintEqualToAnchor:_form.contentLayoutGuide.leadingAnchor constant:24],
        [stack.trailingAnchor constraintEqualToAnchor:_form.contentLayoutGuide.trailingAnchor constant:-24],
        [stack.topAnchor constraintEqualToAnchor:_form.contentLayoutGuide.topAnchor constant:20],
        [stack.bottomAnchor constraintEqualToAnchor:_form.contentLayoutGuide.bottomAnchor constant:-20],
        [stack.widthAnchor constraintEqualToAnchor:_form.frameLayoutGuide.widthAnchor constant:-48]
    ]];
    NSNotificationCenter *center = NSNotificationCenter.defaultCenter;
    [center addObserver:self selector:@selector(activate:) name:UIApplicationDidBecomeActiveNotification object:nil];
    [center addObserver:self selector:@selector(deactivate:) name:UIApplicationWillResignActiveNotification object:nil];
    _active = UIApplication.sharedApplication.applicationState == UIApplicationStateActive;
}

- (UIInterfaceOrientationMask)supportedInterfaceOrientations { return UIInterfaceOrientationMaskLandscape; }
- (BOOL)prefersStatusBarHidden { return YES; }

- (void)connect {
    if (_starting || _running || !_active) return;
    NSString *server = [_server.text stringByTrimmingCharactersInSet:NSCharacterSet.whitespaceAndNewlineCharacterSet];
    NSString *token = _token.text ?: @"";
    NSCharacterSet *valid = [NSCharacterSet characterSetWithCharactersInString:
        @"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"];
    if (!TTValidServer(server) || token.length != 43 ||
        [token rangeOfCharacterFromSet:valid.invertedSet].location != NSNotFound) {
        _status.text = @"Enter a private IPv4 address and the 43-character player token.";
        return;
    }
    [self.view endEditing:YES];
    _starting = YES;
    _connect.enabled = NO;
    _token.text = @""; // Token is memory-only; never save it to preferences/logs.
    _status.text = @"Starting the game…";
    // Let UIKit commit the status change before synchronous engine initialization.
    dispatch_async(dispatch_get_main_queue(), ^{
        if (!self->_active) {
            self->_starting = NO;
            self->_connect.enabled = YES;
            self->_status.text = @"Return to the app and enter your token to connect.";
            return;
        }
        NSError *error = nil;
        NSURL *data = [[NSFileManager defaultManager] URLForDirectory:NSApplicationSupportDirectory
            inDomain:NSUserDomainMask appropriateForURL:nil create:YES error:&error];
        self->_runtime = [[TTEmbeddedRuntime alloc] init];
        if (!data || ![self->_runtime prepareWithBundle:NSBundle.mainBundle
                userData:[data URLByAppendingPathComponent:@"OpenToontown" isDirectory:YES]
                server:server token:token error:&error]) {
            [self fail:error];
            return;
        }
        if (!TTConfigureGraphicsHost(self->_gameContainer)) {
            [self fail:nil];
            return;
        }
        TTSetGraphicsActive(YES);
        AVAudioSession *audio = AVAudioSession.sharedInstance;
        if (![audio setCategory:AVAudioSessionCategoryPlayback error:&error] ||
            ![audio setActive:YES error:&error]) {
            [self fail:error];
            return;
        }
        if (![self->_runtime start:&error]) {
            [self fail:error];
            return;
        }
        self->_input = [[TTGameInputBridge alloc] initWithControlsView:self->_controls error:&error];
        if (!self->_input) { [self fail:error]; return; }
        __weak TTGameViewController *weakSelf = self;
        self->_input.inputFailed = ^(NSError *failure) {
            // Do not destroy Python input while its error callback is on-stack.
            dispatch_async(dispatch_get_main_queue(), ^{ [weakSelf fail:failure]; });
        };
        self->_starting = NO;
        self->_running = YES;
        self->_form.hidden = YES;
        [[NSUserDefaults standardUserDefaults] setObject:server forKey:@"privateServer"];
        TTFrameTarget *target = [[TTFrameTarget alloc] init];
        target.owner = self;
        self->_displayLink = [CADisplayLink displayLinkWithTarget:target selector:@selector(tick:)];
        self->_displayLink.preferredFramesPerSecond = 60;
        [self->_displayLink addToRunLoop:NSRunLoop.mainRunLoop forMode:NSRunLoopCommonModes];
    });
}

- (void)setMovementEnabled:(BOOL)enabled {
    if (_movementEnabled == enabled) return;
    _movementEnabled = enabled;
    [_input setActive:enabled];
    _controls.hidden = !enabled;
}

- (void)copyDiagnostic {
    // Status contains exception type/source locations, never token or locals.
    UIPasteboard.generalPasteboard.string = _status.text;
}

- (void)frame:(CADisplayLink *)link {
    if (!_running || !_active || _inFrame) return;
    @autoreleasepool {
        _inFrame = YES;
        NSError *error = nil;
        BOOL movement = NO;
        BOOL success = [_runtime frameAllowingMovement:&movement error:&error];
        _inFrame = NO;
        if (!success) { [self fail:error]; return; }
        [self setMovementEnabled:movement];
    }
}

- (void)deactivate:(NSNotification *)notification {
    _active = NO;
    _displayLink.paused = YES;
    [self setMovementEnabled:NO];
    TTSetGraphicsActive(NO);
    if (_running) {
        NSError *error = nil;
        if (![_runtime pause:&error]) [self fail:error];
    }
}

- (void)activate:(NSNotification *)notification {
    _active = YES;
    if (_cleanupPending) {
        _cleanupPending = NO;
        NSError *error = _pendingError;
        _pendingError = nil;
        [self fail:error];
        return;
    }
    if (!_running) return;
    TTSetGraphicsActive(YES);
    NSError *error = nil;
    if (![_runtime resume:&error]) { [self fail:error]; return; }
    // The next game frame re-evaluates movement permission; don't resume held keys.
    _displayLink.paused = NO;
}

- (void)fail:(NSError * _Nullable)error {
    [_displayLink invalidate];
    _displayLink = nil;
    [self setMovementEnabled:NO];
    [_input invalidate];
    _input = nil;
    TTSetGraphicsActive(NO);
    _running = NO;
    if (UIApplication.sharedApplication.applicationState == UIApplicationStateBackground) {
        // Panda window teardown can submit GL commands. Defer it until active.
        _cleanupPending = YES;
        _pendingError = error;
        return;
    }
    [_runtime stop];
    _runtime = nil;
    TTClearGraphicsHost();
    _starting = NO;
    _form.hidden = NO;
    _connect.enabled = NO; // Panda does not support interpreter restarts safely.
    _status.text = error.localizedDescription ?: @"The game could not start. Close and reopen the app.";
    _copyDiagnostic.hidden = NO;
}

- (void)dealloc {
    [_displayLink invalidate];
    [NSNotificationCenter.defaultCenter removeObserver:self];
}
@end
