import moderngl
import moderngl_window
import numpy as np


class WormRenderer(moderngl_window.WindowConfig):

    window_size = (1200, 800)
    title = "Worm Simulator GPU"
    gl_version = (3, 3)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.program = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_pos;

                void main() {
                    gl_Position = vec4(in_pos, 0.0, 1.0);
                    gl_PointSize = 40.0;
                }
            """,
            fragment_shader="""
                #version 330
                out vec4 fragColor;

                void main() {
                    fragColor = vec4(1.0, 0.3, 0.3, 1.0);
                }
            """,
        )

        points = np.array([
            [-0.8, -0.8],
            [-0.8,  0.8],
            [ 0.8, -0.8],
            [ 0.8,  0.8],
            [ 0.0,  0.0],
        ], dtype="f4")

        self.vbo = self.ctx.buffer(points.tobytes())
        self.vao = self.ctx.simple_vertex_array(self.program, self.vbo, "in_pos")

    def render(self, time, frame_time):

        self.ctx.clear(0.1, 0.1, 0.1)

        self.vao.render(moderngl.POINTS)

    def on_render(self, time, frame_time):
        # Keep compatibility with moderngl-window builds that call on_render.
        self.render(time, frame_time)


if __name__ == "__main__":
    moderngl_window.run_window_config(WormRenderer)
