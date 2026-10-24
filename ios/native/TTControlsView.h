#import <UIKit/UIKit.h>

NS_ASSUME_NONNULL_BEGIN

@class TTControlsView;

/// The app host forwards these main-thread callbacks to the game input router.
@protocol TTControlsViewDelegate <NSObject>
- (void)controlsView:(TTControlsView *)view movedStickX:(CGFloat)x y:(CGFloat)y;
- (void)controlsView:(TTControlsView *)view jumpPressed:(BOOL)pressed;
@end

/// Landscape overlay. Empty areas pass through to the engine's pointer view.
/// This supplies UIKit controls, not the still-required Panda window bridge.
@interface TTControlsView : UIView
@property(nonatomic, weak, nullable) id<TTControlsViewDelegate> delegate;
@property(nonatomic, getter=isGameplayEnabled) BOOL gameplayEnabled;
- (void)cancelAllTouches;
@end

NS_ASSUME_NONNULL_END
