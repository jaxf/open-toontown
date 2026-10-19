#include "TTBuiltinModules.h"
void TTRegisterGraphicsPipe(void);

// Link-only device executable. Not an app, not installed or executed in CI.
// Referencing every module initializer forces the linker to resolve the
// generated wrappers and their underlying native engine implementations.
int main() {
  TTRegisterGraphicsPipe();
  TTRegisterAudioBackend();
  return TTRegisterBuiltinModules() == 0 ? 0 : 1;
}
