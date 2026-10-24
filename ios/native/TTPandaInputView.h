#import <UIKit/UIKit.h>

#ifdef __cplusplus
class GraphicsWindowInputDevice;
#endif

NS_ASSUME_NONNULL_BEGIN

/// Base view for the future Panda drawable. The host adds TTControlsView above
/// this view. Only touches not captured by that overlay become mouse input.
@interface TTPandaInputView : UIView
#ifdef __cplusplus
/// Device must also be attached to the Panda GraphicsWindow. Main thread only.
- (void)attachInputDevice:(GraphicsWindowInputDevice * _Nullable)device;
#endif
/// Actual framebuffer pixel dimensions, supplied by the renderer on resize.
@property(nonatomic) CGSize drawableSize;
@property(nonatomic, getter=isInputEnabled) BOOL inputEnabled;
- (void)cancelPointer;
@end

NS_ASSUME_NONNULL_END
