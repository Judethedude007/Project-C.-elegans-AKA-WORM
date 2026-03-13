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
                in vec3 in_color;
                out vec3 v_color;

                void main() {
                    gl_Position = vec4(in_pos, 0.0, 1.0);
                    gl_PointSize = 6.0;
                    v_color = in_color;
                }
            """,
            fragment_shader="""
                #version 330
                in vec3 v_color;
                out vec4 fragColor;

                void main() {
                    vec2 c = gl_PointCoord - vec2(0.5);
                    if (dot(c, c) > 0.25) {
                        discard;
                    }
                    fragColor = vec4(v_color, 1.0);
                }
            """,
        )

        self.max_points = 20000
        self.vbo = self.ctx.buffer(reserve=self.max_points * 5 * 4)
        self.vao = self.ctx.vertex_array(
            self.program,
            [
                (self.vbo, "2f 3f", "in_pos", "in_color"),
            ],
        )

    def _world_to_ndc(self, world_positions, camera_x, camera_y, zoom):
        if len(world_positions) == 0:
            return np.empty((0, 2), dtype=np.float32)

        sx = (world_positions[:, 0] - camera_x) * zoom
        sy = (world_positions[:, 1] - camera_y) * zoom

        ndc_x = (sx / (self.width * 0.5)) - 1.0
        ndc_y = 1.0 - (sy / (self.height * 0.5))

        return np.column_stack((ndc_x, ndc_y)).astype(np.float32)

    def render(self, worm_positions, camera_x, camera_y, zoom):
        self.ctx.clear(0.18, 0.14, 0.08, 1.0)

        if worm_positions.size == 0:
            return

        ndc = self._world_to_ndc(worm_positions, camera_x, camera_y, zoom)

        colors = np.tile(np.array([[1.0, 0.55, 0.55]], dtype=np.float32), (ndc.shape[0], 1))
        data = np.hstack((ndc, colors)).astype(np.float32)

        points = min(len(data), self.max_points)
        self.vbo.write(data[:points].tobytes())
        self.vao.render(mode=moderngl.POINTS, vertices=points)
