import numpy as np
from copy import copy
from PIL.Image import fromarray
from cv2 import (fillConvexPoly,
                 getAffineTransform,
                 warpAffine,
                 BORDER_REFLECT_101)


class Triangles:
    def __init__(self):
        """
        Each triangle is a tuple of coordinates
        self.end_coords: masks for each triangle in the end image
        self.start_coords: masks for each triangle in the start image
        self.match: mapping of the triangles in the images
        """
        self.match = {
            ((3, 3), (511, 511), (511, 3)): ((512, 3), (1023, 511), (1023, 3)),
            ((3, 3), (3, 511), (511, 511)): ((512, 3), (512, 511), (1023, 511))
        }

        self.size = 512
        self.end_coords = {}
        self.start_coords = {}

    def _sign(self, triangle):
        p1, p2, p3 = triangle
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

    def _in_triangle(self, pt, triangle):
        v1, v2, v3 = triangle
        sign_1 = self._sign((pt, v1, v2)) <= 0
        sign_2 = self._sign((pt, v2, v3)) <= 0
        sign_3 = self._sign((pt, v3, v1)) <= 0

        return (sign_1 == sign_2) and (sign_2 == sign_3)

    def _find_triangle(self, point, mode='start'):
        triangles = self.match
        if mode != 'start':
            triangles = self.match.values()

        for triangle in triangles:
            if self._in_triangle(point, triangle):
                return triangle

    def _triangle_circumcircle(self, triangle):
        t = np.array(triangle).T
        center = np.zeros(2)
        a = np.sqrt((t[0][0] - t[0][1])**2 + (t[1][0] - t[1][1])**2)
        b = np.sqrt((t[0][1] - t[0][2])**2 + (t[1][1] - t[1][2])**2)
        c = np.sqrt((t[0][2] - t[0][0])**2 + (t[1][2] - t[1][0])**2)

        bot = (a + b + c) * (- a + b + c) * (a - b + c) * (a + b - c)
        if bot < 0.001:
            return (tuple(center), -1.0)
        r = a * b * c / np.sqrt(bot)
        f = np.zeros(2)
        f[0] = (t[0][1] - t[0, 0])**2 + (t[1, 1] - t[1][0])**2
        f[1] = (t[0, 2] - t[0, 0])**2 + (t[1, 2] - t[1][0])**2

        top = np.zeros(2)
        top[0] = (t[1, 2] - t[1][0]) * f[0] - (t[1][1] - t[1][0]) * f[1]
        top[1] = -(t[0, 2] - t[0][0]) * f[0] + (t[0][1] - t[0][0]) * f[1]
        det = (t[1][2] - t[1][0]) * (t[0][1] - t[0][0]) \
              - (t[1][1] - t[1][0]) * (t[0][2] - t[0][0])

        center[0] = t[0][0] + 0.5 * top[0] / det
        center[1] = t[1][0] + 0.5 * top[1] / det
        return (tuple(center), r)

    def _triangle_in_circle(self, circle, triangle):
        for point in triangle:
            if ((point[0] - circle[0][0])**2 + (point[1] - circle[0][1])**2) > circle[1]**2+1:
                return False
        return True

    def _get_common_edge(self, triangle1, triangle2, eps=0.001):
        ids1 = set()
        ids2 = set()
        for i in range(3):
            for j in range(3):
                if triangle1[i] == triangle2[j]:
                    ids1.add(i)
                    ids2.add(j)

        all_ids = set(range(3))
        rest = list(all_ids - ids1) + list(all_ids - ids2)
        return rest

    def _flip_edge(self, rest, triangle1, triangle2):
        j1, j2 = (rest[0] - 1) % 3, (rest[0] + 1) % 3

        new_tr1 = (
            tuple(triangle1[rest[0]]),
            tuple(triangle2[rest[1]]),
            tuple(triangle1[j1])
        )

        new_tr2 = (
            tuple(triangle1[rest[0]]),
            tuple(triangle2[rest[1]]),
            tuple(triangle1[j2])
        )
        return new_tr1, new_tr2

    def _check_delaunay(self, triangle):
        """
        Finding circumcircle of the triangle anf checking all triangles to be not in the circle
        (if bad triangle is found, flip the edge)
        """
        circle = self._triangle_circumcircle(triangle)
        for start in self.match:
            if start != triangle and self._triangle_in_circle(circle, start):
                edge = self._get_common_edge(triangle, start)
                if len(edge) == 2:
                    tr1, tr2 = self._flip_edge(edge, triangle, start)
                    end1, end2 = self.match.pop(triangle), self.match.pop(start)

                    edge_end = self._get_common_edge(end1, end2)
                    end1, end2 = self._flip_edge(edge_end, end1, end2)

                    self.match.update({
                        tr1: end1,
                        tr2: end2
                    })
                    return

    def _split_triangles(self, triangle_start, start, end):
        """
        Split start_triangle into 3
        """
        new_triangles = []
        triangle_end = self.match.pop(triangle_start)

        for i in range(3):
            new_start = (triangle_start[i], triangle_start[(i + 1) % 3], start)
            new_end = (triangle_end[i], triangle_end[(i + 1) % 3], end)
            self.match.update({new_start: new_end})
            new_triangles.append(new_start)
        return new_triangles

    def _check(self, start, end):
        return not(start[0] > self.size or start[1] > self.size
                   or end[1] > self.size or end[0] < self.size)

    def add_point(self, start, end):
        """
        Adding constraint point
        Finding the triangle to insert the point
        Running checking and updating delaunay triangulation (self._check_delaunay)
        """
        if not self._check(start, end):
            return

        triangle_start = self._find_triangle(start)
        if triangle_start is None :
            return
        new_triangles = self._split_triangles(triangle_start, start, end)

        for triangle in new_triangles:
            self._check_delaunay(triangle)

    def determine_coords(self, img1, img2, tau):
        """
        Changing color in each triangle
        First, the mask for start and end triangles are computed
        After that, I change the colors of the first triangle corresponding to the second, calling self.update_images
        """
        arr_img1 = np.array(img1, dtype=np.float64)
        arr_img2 = np.array(img2, dtype=np.float64)
        for start, end in self.match.items():
            start_triangle = np.array(start)
            end_triangle = np.array(end)
            self.start_coords.update({
                start: fillConvexPoly(np.zeros((self.size, self.size)), start_triangle, 1)
            })

            local_end = copy(end_triangle)
            for i in range(3):
                local_end[i][0] -= 512

            self.end_coords.update({
                end: fillConvexPoly(np.zeros((self.size, self.size)), local_end, 1)
            })
            self._update_image(start, end, local_end, arr_img1, arr_img2, tau)

        return fromarray(arr_img1.astype(np.uint8))

    def _update_image(self, start, end, local_end,  img1, img2, t):
        """
        Using Affine Transform (Barycentric coordinates) for changing start triangle
        """
        triangle_end = np.array(local_end, dtype=np.float32)
        triangle_start = np.array(start, dtype=np.float32)
        warpMat = getAffineTransform(triangle_end, triangle_start)

        mask_start = self.start_coords[start]
        mask_end = self.end_coords[end]

        triangle_img1 = np.multiply(np.expand_dims(mask_start, -1), img1)
        img1 -= triangle_img1

        triangle_img2 = np.multiply(np.expand_dims(mask_end, -1), img2)

        updated_img2 = warpAffine(triangle_img2,
                                  warpMat,
                                  (self.size, self.size),
                                  borderMode=BORDER_REFLECT_101)

        img1 += (t * updated_img2 + (1 - t) * triangle_img1)

