#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from mapinfo import MapInfo
from random import randint
from scipy.spatial import cKDTree
import math
import aer1516

class RRT(object):
    def __init__(self, q_init):
        self._root = q_init
        self._rrt = {q_init:q_init}

    def search_nearest_vertex(self, p):
        rrt_list = self._rrt.items()
        distance = [(q[0][0] - p[0]) ** 2 + (q[0][1] - p[1]) ** 2 for q in rrt_list]
        idx = distance.index(min(distance))
        return list(rrt_list)[idx][0]

    def is_contain(self, q):
        return q in self._rrt

    def is_root(self, q):
        return q == self._root

    def add(self, q_new, q_near):
        self._rrt[q_new] = q_near

    def get_rrt(self):
        return self._rrt

    def get_parent(self, q):
        return self._rrt[q]

    def extend(self, q_rand, okdtree):
        # find nearest point in rrt
        q_near = self.search_nearest_vertex(q_rand)
        # calc new vertex
        q_new = self._calc_new_point(q_near, q_rand, delta_q=2.0)
        if is_collision(q_new, okdtree):
            return None
        self.add(q_new, q_near)
        return q_new

    def _calc_new_point(self, q_near, q_rand, delta_q=1.0):
        if distance(q_near, q_rand) < delta_q:
            return q_rand
        angle = math.atan2(q_rand[1] - q_near[1], q_rand[0] - q_near[0])
        q_new = (q_near[0] + math.cos(angle), q_near[1] + math.sin(angle))
        return q_new

def is_collision(p, okdtree):
    d, _ = okdtree.query(p)
    return d <= 1.0

def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def reconstruct_path(rrt, end):
    path = []
    q = end
    while not rrt.is_root(q):
        path.append(q)
        q = rrt.get_parent(q)
    path.append(q)
    return path

def rrt_planning(map_info, display=False, points_generator_type=aer1516.RandomPointsGenerator, stats=None):
    rrt = RRT(map_info.start)
    okdtree = cKDTree(map_info.obstacle)

    points_generator = points_generator_type(map_info, rrt, map_info.end, visualize=display)

    if stats != None: stats.start()
    for _ in range(10000):
        if stats != None: stats.iterate()

        # generate random point
        if randint(0, 10) > 2:
            q_rand = points_generator.generate_point()
            if q_rand == map_info.start or q_rand in map_info.obstacle or rrt.is_contain(q_rand):
                points_generator.report_invalid_point()
                continue
        else:
            q_rand = map_info.end

        q_new = rrt.extend(q_rand, okdtree)
        if not q_new:
            points_generator.report_invalid_point()
            continue

        # reset skips
        points_generator.report_successful_point()

        if display:
            map_info.set_rand(q_rand)
            map_info.set_rrt(rrt.get_rrt())
        # check goal
        if distance(q_new, map_info.end) <= 1.0:
            if q_new != map_info.end:
                rrt.add(map_info.end, q_new)
            if stats != None: stats.end()
            final_path = reconstruct_path(rrt, map_info.end)

            if stats != None: stats.final_path(final_path)
            if stats != None: stats.rrt(rrt.get_rrt())
            return final_path

    if stats != None: stats.end()
    return None

if __name__ == "__main__":
    m = MapInfo(50, 50)
    m.show()
    m.start = (10, 10)
    m.end = (40, 40)
    m.obstacle = [(15, i) for i in range(30)] + [(35, 50 - i) for i in range(30)]
    input('press enter to start...')
    m.path = rrt_planning(m, display=True)
    print('success!')
    m.wait_close()
