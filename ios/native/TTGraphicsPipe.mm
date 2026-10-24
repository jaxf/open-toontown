// UIKit must precede Panda's network headers (TCP_NODELAY macro collision).
#import "TTGraphicsHost.h"
#import "TTGLESView.h"
#include "graphicsEngine.h"
#include "graphicsPipeSelection.h"
#include "graphicsWindow.h"
#include "graphicsWindowInputDevice.h"
#include "gles2gsg.h"
#include <dlfcn.h>

static __weak UIView *tt_container;
static __weak TTGLESView *tt_drawable;
static bool tt_active = false;

class TTStateGuardian final : public GLES2GraphicsStateGuardian {
public:
    TTStateGuardian(GraphicsEngine *engine, GraphicsPipe *pipe) :
        GLES2GraphicsStateGuardian(engine, pipe) {}
protected:
    void *do_get_extension_func(const char *name) override {
        return dlsym(RTLD_DEFAULT, name);
    }
};

class TTGraphicsWindow final : public GraphicsWindow {
public:
    TTGraphicsWindow(GraphicsEngine *engine, GraphicsPipe *pipe, const std::string &name,
                     const FrameBufferProperties &fb, const WindowProperties &wp, int flags) :
        GraphicsWindow(engine, pipe, name, fb, wp, flags, nullptr, nullptr) {
        // Keep device zero stable if Panda closes and reopens this output.
        _input = GraphicsWindowInputDevice::pointer_and_keyboard(this, "touch");
        add_input_device(_input);
    }

    bool begin_frame(FrameMode mode, Thread *thread) override {
        if (!NSThread.isMainThread || _gsg == nullptr || ![_view prepareDrawable]) return false;
        CGSize size = _view.drawableSize;
        if (get_x_size() != (int)size.width || get_y_size() != (int)size.height)
            system_changed_size((int)size.width, (int)size.height);
        auto *gsg = static_cast<TTStateGuardian *>(_gsg.p());
        gsg->reset_if_new();
        // iOS presents a nonzero FBO. Never assume framebuffer zero is a screen.
        // Bind via Panda so its cached FBO agrees, including after texture passes.
        gsg->bind_fbo(_view.framebuffer);
        gsg->set_current_properties(&get_fb_properties());
        if (mode == FM_render) clear_cube_map_selection();
        return gsg->begin_frame(thread);
    }

    void end_frame(FrameMode mode, Thread *thread) override {
        if (mode == FM_render) copy_to_textures();
        _gsg->end_frame(thread);
        if (mode == FM_render) {
            trigger_flip();
            clear_cube_map_selection();
        }
    }

    void end_flip() override {
        if (_flip_ready) [_view presentDrawable];
        GraphicsWindow::end_flip();
    }

    void process_events() override {
        if (!NSThread.isMainThread) return;
        GraphicsWindow::process_events();
        if (!_view) return;
        bool foreground = _view.isRenderingEnabled &&
            UIApplication.sharedApplication.applicationState == UIApplicationStateActive;
        if (_properties.get_foreground() != foreground) {
            WindowProperties props;
            props.set_foreground(foreground);
            system_changed_properties(props);
        }
    }

protected:
    bool open_window() override {
        UIView *container = tt_container;
        if (!NSThread.isMainThread || !container || !container.window || tt_drawable ||
            !_engine->get_threading_model().get_draw_name().empty()) return false;
        _view = [[TTGLESView alloc] initWithFrame:container.bounds];
        if (!_view) return false;
        _view.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
        [container insertSubview:_view atIndex:0];
        _view.renderingEnabled = tt_active;
        [_view layoutIfNeeded];
        if (![_view prepareDrawable]) {
            [_view destroyDrawable];
            [_view removeFromSuperview];
            _view = nil;
            return false;
        }
        _gsg = new TTStateGuardian(_engine, _pipe);
        [_view attachInputDevice:_input];
        _view.inputEnabled = YES;
        tt_drawable = _view;
        _fb_properties.clear();
        _fb_properties.set_rgb_color(true);
        _fb_properties.set_rgba_bits(8, 8, 8, 8);
        _fb_properties.set_depth_bits(24);
        _fb_properties.set_stencil_bits(8);
        _fb_properties.set_back_buffers(1);
        _fb_properties.set_force_hardware(true);
        _properties.set_origin(0, 0);
        _properties.set_size((int)_view.drawableSize.width, (int)_view.drawableSize.height);
        _properties.set_foreground(true);
        _properties.set_minimized(false);
        _properties.set_open(true);
        return true;
    }

    void close_window() override {
        // The application host must remove outputs before finalizing Python,
        // on this thread while still in the foreground. Suspension keeps them.
        [_view makeCurrent];
        [_view attachInputDevice:nullptr];
        _gsg.clear();
        [_view destroyDrawable];
        [_view removeFromSuperview];
        tt_drawable = nil;
        _view = nil;
        GraphicsWindow::close_window();
    }

private:
    PT(GraphicsWindowInputDevice) _input;
    TTGLESView *__strong _view = nil;
};

class TTGraphicsPipe final : public GraphicsPipe {
public:
    TTGraphicsPipe() {
        _is_valid = tt_container != nil;
        _supported_types = OT_window | OT_fullscreen_window | OT_buffer | OT_texture_buffer;
    }
    std::string get_interface_name() const override { return "Toontown UIKit OpenGL ES 2"; }
    PreferredWindowThread get_preferred_window_thread() const override { return PWT_app; }
    static PT(GraphicsPipe) construct() { return new TTGraphicsPipe; }
    static TypeHandle get_class_type() { return _type; }
    static void init_type() {
        GraphicsPipe::init_type();
        register_type(_type, "TTGraphicsPipe", GraphicsPipe::get_class_type());
    }
    TypeHandle get_type() const override { return _type; }
    TypeHandle force_init_type() override { init_type(); return _type; }
protected:
    PT(GraphicsOutput) make_output(const std::string &name, const FrameBufferProperties &fb,
            const WindowProperties &wp, int flags, GraphicsEngine *engine,
            GraphicsStateGuardian *gsg, GraphicsOutput *host, int retry, bool &precertify) override {
        precertify = false;
        if (!_is_valid || !NSThread.isMainThread ||
            !engine->get_threading_model().get_draw_name().empty()) return nullptr;
        if (retry == 0) {
            const int unsupported = BF_refuse_window | BF_require_parasite | BF_require_callback_window |
                BF_can_bind_color | BF_can_bind_every | BF_can_bind_layered | BF_rtt_cumulative |
                BF_size_track_host | BF_size_square | BF_size_power_2;
            if ((flags & unsupported) || gsg || host || tt_drawable) return nullptr;
            return new TTGraphicsWindow(engine, this, name, fb, wp, flags);
        }
        // Texture buffers share the host's context; no second UIKit window.
        if (retry == 1 && host && host->get_pipe() == this && host->get_engine() == engine &&
            host->get_gsg() && (!gsg || gsg == host->get_gsg()) &&
            !(flags & (BF_require_window | BF_require_parasite | BF_require_callback_window))) {
            return new GLES2GraphicsBuffer(engine, this, name, fb, wp, flags, host->get_gsg(), host);
        }
        return nullptr;
    }
private:
    static TypeHandle _type;
};
TypeHandle TTGraphicsPipe::_type;

void TTRegisterGraphicsPipe(void) {
    static bool registered = false;
    if (registered) return;
    init_libgles2gsg();
    TTGraphicsPipe::init_type();
    GraphicsPipeSelection::get_global_ptr()->add_pipe_type(TTGraphicsPipe::get_class_type(),
                                                          TTGraphicsPipe::construct);
    registered = true;
}

BOOL TTConfigureGraphicsHost(UIView *container) {
    if (!NSThread.isMainThread || !container || tt_drawable) return NO;
    tt_container = container;
    tt_active = false;
    TTRegisterGraphicsPipe();
    return YES;
}

void TTSetGraphicsActive(BOOL active) {
    if (!NSThread.isMainThread) return;
    tt_active = active && UIApplication.sharedApplication.applicationState == UIApplicationStateActive;
    tt_drawable.renderingEnabled = tt_active;
    tt_drawable.inputEnabled = tt_active;
}

BOOL TTClearGraphicsHost(void) {
    if (!NSThread.isMainThread || tt_drawable) return NO;
    tt_container = nil;
    tt_active = false;
    return YES;
}
