#include "TTBuiltinModules.h"
#include "httpClient.h"
#ifndef HAVE_OPENSSL
#error The game imports HTTPClient and requires OpenSSL support
#endif
void TTRegisterGraphicsPipe(void);

// Link-only device executable. Not an app, not installed or executed in CI.
// Referencing every module initializer forces the linker to resolve the
// generated wrappers and their underlying native engine implementations.
int main() {
  TTRegisterGraphicsPipe();
  TTRegisterAudioBackend();
  if (HTTPClient::get_global_ptr() == nullptr) return 1;
  return TTRegisterBuiltinModules() == 0 ? 0 : 1;
}
