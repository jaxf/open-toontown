#ifndef TT_BUILTIN_MODULES_H
#define TT_BUILTIN_MODULES_H

/// Register statically linked engine modules before initializing Python.
/// Returns -1 if Python has already started or registration fails.
int TTRegisterBuiltinModules(void);

/// Register the linked OpenAL factory before the game creates audio managers.
void TTRegisterAudioBackend(void);

#endif
