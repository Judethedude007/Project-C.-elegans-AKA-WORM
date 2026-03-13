import numpy as np
import moderngl
from config import WORLD_SIZE


class GPURenderer:

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.ctx.line_width = 2.0

        self.program = self.ctx.program(
            vertex_shader="""
                #version 330
                uniform vec2 camera;
                uniform float zoom;
                in vec2 in_pos;

                void main()
                {
                    vec2 pos = (in_pos - camera) * zoom;
                    gl_Position = vec4(pos, 0.0, 1.0);
                    gl_PointSize = 8.0;
                }
            """,
            fragment_shader="""
                #version 330
                uniform vec3 color;
                out vec4 fragColor;

                void main() {
                    fragColor = vec4(color, 1.0);
                }
            """,
        )

        self.max_vertices = 300000
        self.vbo = self.ctx.buffer(reserve=self.max_vertices * 2 * 4)
        self.vao = self.ctx.simple_vertex_array(self.program, self.vbo, "in_pos")

        self.program["camera"].value = (0.0, 0.0)
        self.program["zoom"].value = 1.0
        self.program["color"].value = (1.0, 0.3, 0.3)

    def _render_vertices(self, vertices, color, mode):
        if vertices.size == 0:
            return

        safe_limit = WORLD_SIZE * 2
        finite_mask = np.isfinite(vertices).all(axis=1)
        bounds_mask = (
            (np.abs(vertices[:, 0]) <= safe_limit)
            & (np.abs(vertices[:, 1]) <= safe_limit)
        )
        safe_vertices = vertices[finite_mask & bounds_mask]

        if safe_vertices.size == 0:
            return

        count = min(len(safe_vertices), self.max_vertices)
        self.program["color"].value = color
        self.vbo.orphan()
        self.vbo.write(safe_vertices[:count].astype("f4").tobytes())
        self.vao.render(mode=mode, vertices=count)

    def render(
        self,
        worm_strips,
        pheromone_positions,
        food_layers,
        chemical_layers,
        head_positions,
        camera_x,
        camera_y,
        zoom,
    ):

        self.ctx.clear(0.05, 0.05, 0.05)

        self.program["camera"].value = (camera_x, camera_y)
        self.program["zoom"].value = zoom

        for vertices, color in food_layers:
            self._render_vertices(vertices, color, moderngl.POINTS)

        for vertices, color in chemical_layers:
            self._render_vertices(vertices, color, moderngl.POINTS)

        self._render_vertices(pheromone_positions, (0.45, 0.6, 0.9), moderngl.POINTS)

        for worm_strip in worm_strips:
            self._render_vertices(worm_strip, (1.0, 1.0, 1.0), moderngl.LINE_STRIP)

        self._render_vertices(head_positions, (1.0, 0.25, 0.25), moderngl.POINTS)
