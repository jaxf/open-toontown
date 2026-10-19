#import "TTGraphicsHost.h"

// Link-only executable. No UIApplication, context, window, or simulator run.
int main() {
    TTRegisterGraphicsPipe();
    return 0;
}
