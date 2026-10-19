#include "TTBuiltinModules.h"
#include <Python.h>

extern "C" PyObject *PyInit_core(void);
extern "C" PyObject *PyInit_direct(void);
extern "C" PyObject *PyInit_physics(void);
extern "C" PyObject *PyInit_ode(void);
extern "C" PyObject *PyInit_otp(void);
extern "C" PyObject *PyInit_toontown(void);

int TTRegisterBuiltinModules(void) {
  if (Py_IsInitialized()) return -1;
  static struct _inittab modules[] = {
    {"panda3d.core", PyInit_core},
    {"panda3d.direct", PyInit_direct},
    {"panda3d.physics", PyInit_physics},
    {"panda3d.ode", PyInit_ode},
    {"panda3d.otp", PyInit_otp},
    {"panda3d.toontown", PyInit_toontown},
    {nullptr, nullptr},
  };
  return PyImport_ExtendInittab(modules);
}
