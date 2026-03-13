class Camera:

    def __init__(self):

        self.x = 0
        self.y = 0
        self.zoom = 1

    def move(self, dx, dy):

        self.x += dx
        self.y += dy

    def apply(self, x, y):

        sx = (x - self.x) * self.zoom
        sy = (y - self.y) * self.zoom

        return sx, sy
