import math
import random
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint


ANGLE_I = math.radians(90.0)
IOR = 1.5
NUM_RAYS = 1000

BOUNCE_COLOR = ['tab:blue','tab:orange', 'tab:green', 'tab:red', 'tab:pink']

class Ray:
    def __init__(self, origin, direction, start=0., end=np.inf):
        """Create a ray with the given origin and direction."""
        self.origin = np.array(origin)
        self.direction = np.array(direction)
        self.start = start
        self.end = end
        self.trace = []

# class Circle:
#     def __init__(self, radius, pos):
#         self.radius = radius
#         self.pos = pos
    
#     def intersect(self, ray):
#         op = self.pos-ray.origin
#         t, eps = 1e-10, 1e-10
#         b = np.dot(op, ray.direction)
#         det = b*b - np.dot(op, op) + self.radius*self.radius

#         if det < 0:
#             return 0.0
#         else:
#             det = math.sqrt(det)
        
#         if b - det > eps:
#             t =  b - det
#         elif b + det > eps:
#             t = b + det
#         else:
#             t = 0.0
        
#         return ray.origin + ray.direction*t

#     def angle_intersect(self, ray):
#         """Angle of intersection with circle in degrees"""
#         p1 = self.intersect(ray)
#         ang_rad = math.atan2(p1[1]-self.pos[1], p1[0]-self.pos[0])
#         return (ang_rad*180.0/math.pi)%360.0

class LineSeg:
    def __init__(self, num, nodes, normals, eta):
        self.num = num # line segment ID
        self.nodes = nodes
        self.normals = normals
        self.eta = eta

    def intersect(self, ray):
        """Computes the intersection between a ray and line segment, if it exists."""
        # print("ACTUAL ORIGIN", ray.origin)
        # print("ACTUAL DIR", ray.direction)
        t, eps, d = 1e20, 1e-10, 1e20

        for i in range(len(self.nodes)-1):
            p1 = self.nodes[i]
            p2 = self.nodes[i+1]

            v1 = np.array([ray.origin - p1])
            v2 = np.array([p2 - p1])
            v3 = np.array([-ray.direction[1], ray.direction[0]])

            if np.dot(v2, v3) < 1e-10 and np.dot(v2, v3) > -1e-10:
                # print("DOT", np.dot(v2, v3))
                return [], None

            t1 = np.cross(v2, v1) / np.dot(v2, v3)
            t2 = np.dot(v1, v3) / np.dot(v2, v3)

            if t1 >= 0.0 and t2 >= 0.0 and t2 <= 1.0:
                point = ray.origin + t1*ray.direction

                if not np.array_equal(point, ray.origin):
                    return point, i
        
        return [], None

def normalize(v):
    return v / np.linalg.norm(v)

def FrDielecric(costhetai, costhetat, etai_parl, etat_parl, etai_perp, etat_perp, entering):
    if not entering:
        temp = etai_parl
        etai_parl = etat_parl
        etat_parl = temp

        temp = etai_perp
        etai_perp = etat_perp
        etat_perp = temp

    rs = ((etai_perp*costhetai) - (etat_perp*costhetat)) / ((etai_perp*costhetai) + (etat_perp*costhetat)) # Rs
    rp = ((etat_parl*costhetai) - (etai_parl*costhetat)) / ((etat_parl*costhetai) + (etai_parl*costhetat)) # Rp
    # print("Rs", rs*rs)
    # print("Rp", rp*rp)
    # print("total", (r_parl*r_parl + r_perp*r_perp) / 2)
    return (rs*rs + rp*rp) / 2

def adj_intersect(intersect, direction):
    return intersect+1e-10*direction

def radiance(ray, ls, depth=0):
    intersection, num_ls = ls.intersect(ray)
    # print("ray origin", ray.origin)
    # print("ray direction", ray.direction)
    # print("intersection", intersection)
    # print("num_ls", num_ls)
    if (intersection == [] or depth > 4):
        return None

    ratio = 0
    n = None
    if num_ls == ls.num-1:
        n = ls.normals[ls.num - 1]*(1 - ratio) + ls.normals[0]*ratio
    else:
        n = ls.normals[num_ls]*(1 - ratio) + ls.normals[num_ls + 1]*ratio
    
    # print("N", n)
    nl = n if np.dot(n, ray.direction) < 0 else -n
    into = np.dot(n, nl) > 0

    nc = 1.0
    nt = ls.eta
    nnt = nc/nt if into else nt/nc
    ddn = np.dot(ray.direction, nl)
    cos2t = 1 - nnt*nnt*(1 - ddn*ddn)

    fresnel = 1
    if cos2t > 0:
        tdir = normalize((ray.direction*nnt - n*((1 if into else -1)*(ddn*nnt + math.sqrt(cos2t)))))
        costhetai = abs(np.dot(nl, ray.direction))
        costhetat = abs(np.dot(nl, tdir))
        fresnel = FrDielecric(costhetai, costhetat, 1.0, ls.eta, 1.0, ls.eta, into)

    # russian roulette
    # depth = depth + 1
    # if depth > 5:
    #     if random.random() > RRprob:
    #         return None
    #     else:
    #         weight = weight / RRprob
    
    # reflection
    if (random.random() < fresnel):
        new_dir = normalize(ray.direction - n*2*np.dot(n,ray.direction))

        # print("org dir::", ray.direction)
        intersection = adj_intersect(intersection, new_dir)
        r = Ray(intersection, new_dir)
        # print("intersection::", intersection)
        # print("new_dir::", new_dir)
        depth = depth + 1
        new_ray = radiance(r, ls, depth)

        if new_ray != None:
            new_ray.trace.append(r)
            return new_ray
        else:
            return r
    # refraction
    else:
        nc = 1.0
        nt = ls.eta
        nnt = nc/nt if into else nt/nc
        ddn = np.dot(ray.direction, nl)
        cos2t = 1 - nnt*nnt*(1 - ddn*ddn)
        if cos2t < 0:
            # return None
            cos2t = -cos2t
        
        tdir = normalize((ray.direction*nnt - n*((1 if into else -1)*(ddn*nnt + math.sqrt(cos2t)))))
        intersection = adj_intersect(intersection, tdir)
        ray = Ray(intersection, tdir)
        new_ray = radiance(ray, ls)

        if new_ray != None:
            new_ray.trace.append(ray)
            return new_ray
        else:
            return ray

# def generate_ray():
#     ox, oy = 2.0*(random.random()-0.5), random.random()
#     rand_origin = np.array([ox, oy])
#     ray_dir = normalize(np.array([0, 0])-rand_origin)

#     if ray_dir[0]==1.0:
#         ray_dir[0] = ray_dir[0] - 1e-10
#     elif ray_dir[0]==-1.0:
#         ray_dir[0] = ray_dir[0] + 1e-10

#     return Ray(rand_origin, ray_dir)

def perp_normal(p1, p2):
    dx = p2[0]-p1[0]
    dy = p2[1]-p1[1]
    
    return normalize([-dy, dx])

def collect_bin_ang(d):
    ang = math.acos(np.dot(np.array(normalize([1, 0])), d))
    if d[1] < 0:
        ang = -ang+2*math.pi
    return math.degrees(ang)

# def generate_ray(ang):
#     ox = (random.random()-0.5)-1
#     oy = 1
#     origin = np.array([ox, oy])
#     # ray_dir = normalize(np.array([math.cos(math.radians(90)-ang), -math.sin(math.radians(90)-ang)]))
#     ray_dir = normalize(np.array([9.99999809e-01-ang, -6.18144403e-04-ang]))
#     return Ray(origin, ray_dir)

def generate_ray(ang):
    wavelength = 650*1e-9
    waist = 170*1e-6
    std = waist/2

    cury = np.random.normal(0, std)
    origin = np.array([0.0, cury])
    divergence = wavelength/(math.sqrt(2)*math.pi*waist)

    beam_angle = np.random.normal(0, divergence/math.sqrt(2))
    direction = normalize(np.array([math.cos(beam_angle)-ang, math.sin(beam_angle)-ang]))

    ray =  Ray(origin, direction) 

    return ray

def plot_ray(ray, return_ray, collect_circ):
    trace_len = len(return_ray.trace)

    r_o = ray.origin
    r_d = ray.direction

    p_end1 = r_o

    p_end2 = return_ray.origin if trace_len < 1 else return_ray.trace[trace_len-1].origin
    
    x, y = [p_end1[0], p_end2[0]], [p_end1[1], p_end2[1]]
    plt.plot(x, y, alpha=0.3, color="grey")

    p_end1 = p_end2

    print("FIRST origin", ray.origin)
    print("FIRST direction", ray.direction)

    if len(return_ray.trace) > 0:
        print("origin", return_ray.trace[trace_len-1].origin)
        print("direction", return_ray.trace[trace_len-1].direction)

        for i in range(1, trace_len):
            r = return_ray.trace[trace_len-1-i]
            print("origin", r.origin)
            print("direction", r.direction)

            p_end2 = r.origin
            
            x, y = [p_end1[0], p_end2[0]], [p_end1[1], p_end2[1]]
            plt.plot(x, y, '--', color=BOUNCE_COLOR[trace_len])

            p_end1 = p_end2

        p_end2 = return_ray.origin

        x, y = [p_end1[0], p_end2[0]], [p_end1[1], p_end2[1]]
        plt.plot(x, y, '--', color=BOUNCE_COLOR[trace_len])

    rr_o = return_ray.origin
    rr_d = return_ray.direction

    p_end1 = rr_o
    p_end2 = rr_o + 1e10*rr_d

    
        # rr_o = return_ray.trace[len(return_ray.trace)-1].origin
        # p_end1 = return_ray.origin
        # p_end2 = return_ray.origin + 1e10*return_ray.direction

    
    x, y = [p_end1[0], p_end2[0]], [p_end1[1], p_end2[1]]
    plt.plot(x, y, '--', color=BOUNCE_COLOR[trace_len])
    

    ang = int(round(collect_bin_ang(return_ray.direction)))
    if ang in collect_circ:
        collect_circ[ang] = collect_circ[ang] + 1        
    else:
        collect_circ[ang] = 1

    

    return collect_circ
    
def makeplot():
    plt.xlim([-5, 5])
    plt.ylim([-5, 5])

    collect_circ = dict([])
    # circ = Circle(1e10, np.array([0, 0]))

    rays = []
    for i in range(NUM_RAYS):
        rays.append(generate_ray(ANGLE_I))

    # rays = [Ray(np.array([-1, 0.0000001]), np.array([0.70710678, 0.70710678]))]

    # p1, p2, p3, p4 = np.array([-5, 10]), np.array([-0.5, -2]), np.array([0.5, -2]), np.array([5, 10])
    # p1, p2, p3, p4 = np.array([10, 0.5]), np.array([-10, 0.5]), np.array([-10, -1]), np.array([10, -1])
    p1, p2, p3, p4 = np.array([-1e10, -2]), np.array([-1, -2]), np.array([1, -2]), np.array([1e10, -2])
    norm1, norm2, norm3 = np.array(perp_normal(p1, p2)), np.array(perp_normal(p2, p3)), np.array(perp_normal(p3, p4))
    print("NORMS", norm1, norm2, norm3)

    # eta = math.sqrt(IOR*IOR - math.sin(theta)*math.sin(theta))/math.cos(theta)
    lineseg = LineSeg(3, [p1, p2, p3, p4], [norm1, norm2, norm3], IOR)
    
    x1, y1 = [p1[0], p2[0]], [p1[1], p2[1]]
    x2, y2 = [p2[0], p3[0]], [p2[1], p3[1]]
    x3, y3 = [p3[0], p4[0]], [p3[1], p4[1]]
    plt.plot(x1, y1, 'black', x2, y2, 'black', x3, y3, 'black')

    num_rays_hit = 0
    for ray in rays:
        # print("ray origin", ray.origin)
        # print("ray direction", ray.direction)

        return_ray = radiance(ray, lineseg)
        
        if return_ray != None:
            num_rays_hit = num_rays_hit + 1
            print("return ray origin", return_ray.origin)
            print("return ray direction", return_ray.direction)
            # print("---------------")s
            # print(return_ray.trace[0].origin)
            # print(return_ray.trace[1].origin)
            

            # r_o = ray.origin
            # r_d = ray.direction

            # rr_o = return_ray.origin
            # rr_d = return_ray.direction

            # p_end1 = rr_o
            # p_end2 = rr_o + 1e10*rr_d
            # if len(return_ray.trace) > 0:
            #     rr_o = return_ray.trace[len(return_ray.trace)-1].origin
            #     p_end1 = return_ray.origin
            #     p_end2 = return_ray.origin + 1e10*return_ray.direction

            # x2, y2 = [r_o[0], rr_o[0]], [r_o[1], rr_o[1]]
            # x3, y3 = [p_end1[0], p_end2[0]], [p_end1[1], p_end2[1]]
            

            # ang = int(round(collect_bin_ang(return_ray.direction)))
            # if ang in collect_circ:
            #     collect_circ[ang] = collect_circ[ang] + 1        
            # else:
            #     collect_circ[ang] = 1

            # print("angle of intersection", ang)
                
            # plt.plot(x2, y2, color="cyan")
            # plt.plot(x3, y3, '--', color="salmon")


            collect_circ = plot_ray(ray, return_ray, collect_circ)


    distr_circ = dict([])
    for k, v in collect_circ.items():
        distr_circ[k] = v/num_rays_hit
    pprint(distr_circ)

    plt.show()


makeplot()

    