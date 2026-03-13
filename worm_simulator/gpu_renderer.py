import numpy as np
import moderngl


class GPURenderer:

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        self.program = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_pos;

                void main() {
                    gl_Position = vec4(in_pos, 0.0, 1.0);
                    gl_PointSize = 8.0;
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

        self.max_points = 120000
        self.vbo = self.ctx.buffer(reserve=self.max_points * 2 * 4)
        self.vao = self.ctx.simple_vertex_array(self.program, self.vbo, "in_pos")

    def render(self, worm_positions, world_size):

        self.ctx.clear(0.05, 0.05, 0.05)

        if worm_positions.size == 0:
            return

        points = np.array(worm_positions, dtype="f4", copy=True)

        # OpenGL uses normalized coordinates in range [-1, 1].
        points[:, 0] = (points[:, 0] / world_size) * 2.0 - 1.0
        points[:, 1] = (points[:, 1] / world_size) * 2.0 - 1.0

        count = min(len(points), self.max_points)
        self.vbo.write(points[:count].tobytes())

        self.vao.render(moderngl.POINTS, vertices=count)
