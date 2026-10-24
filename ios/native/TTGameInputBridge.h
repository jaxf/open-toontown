#import "TTControlsView.h"

NS_ASSUME_NONNULL_BEGIN

/// Own on the main engine/UI thread after Python and the mobile client start.
/// Invalidate before Python finalization. The host must retain this bridge.
@interface TTGameInputBridge : NSObject <TTControlsViewDelegate>
- (nullable instancetype)initWithControlsView:(TTControlsView *)view
                                       error:(NSError * _Nullable * _Nullable)error;
- (instancetype)init NS_UNAVAILABLE;
@property(nonatomic, copy, nullable) void (^inputFailed)(NSError *error);
/// Enable only while gameplay accepts movement; disable for chat and menus.
/// The host must explicitly re-enable after an app suspension.
- (void)setActive:(BOOL)active;
- (void)invalidate;
@end

NS_ASSUME_NONNULL_END
