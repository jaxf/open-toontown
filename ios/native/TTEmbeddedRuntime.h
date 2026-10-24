#pragma once
#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN
/// Own and call on the main thread. One interpreter/game attempt per process.
@interface TTEmbeddedRuntime : NSObject
- (BOOL)prepareWithBundle:(NSBundle *)bundle userData:(NSURL *)userData
                  server:(NSString *)server token:(NSString *)token
                   error:(NSError * _Nullable * _Nullable)error;
- (BOOL)start:(NSError * _Nullable * _Nullable)error;
- (BOOL)frameAllowingMovement:(BOOL *)allowed error:(NSError * _Nullable * _Nullable)error;
- (BOOL)pause:(NSError * _Nullable * _Nullable)error;
- (BOOL)resume:(NSError * _Nullable * _Nullable)error;
/// Foreground teardown. Keeps Python alive; Panda cannot safely be reinitialized.
- (void)stop;
@end
NS_ASSUME_NONNULL_END
