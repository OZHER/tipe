from numpy import sin, cos, pi
from utils import v_sum, v_sub, scalar_mul, v_list_sum, change_basis, norm
from constants import *


class Bone:
    def __init__(self, index, length, theta0, mass, color):
        self.index = index
        self.r = length
        self.m = mass
        self.theta = theta0
        self.l_theta = [theta0, theta0, theta0]
        self.color = color
        self.J = 1 / 12 * mass * length ** 2  # moment of inertia for the axis around the center of gravity
        self.Ep0 = 0  # set it later
        self.muscles = []  # set it later

    def origin(self, bones):
        if self.index == 0:
            return [0, 0]
        else:
            return bones[self.index - 1].end(bones)

    def end(self, bones):
        return v_sum(self.origin(bones), [self.r * sin(self.theta), - self.r * cos(self.theta)])

    def e_theta(self):  # coordinates of the eth vector
        return [cos(self.theta), sin(self.theta)]

    def e_r(self):  # coordinates of the eth vector
        return [sin(self.theta), -cos(self.theta)]

    def G(self, bones):  # coordinates of the gravity center
        return scalar_mul(0.5, v_sum(self.origin(bones), self.end(bones)))

    def relative_to_absolute_matrix(self):
        return [[sin(self.theta), cos(self.theta)], [- cos(self.theta), sin(self.theta)]]

    def theta_dot(self):
        return (self.l_theta[-1] - self.l_theta[-2]) / t

    def theta_2dot(self):
        return (self.l_theta[-1] - 2*self.l_theta[-2] + self.l_theta[-3]) / t**2

    def G_dot(self, bones):  # velocity of the center of gravity
        return v_sum(scalar_mul(0.5 * self.r * self.theta_dot(), self.e_theta()),
                     v_list_sum([scalar_mul(bones[i].r * bones[i].theta_dot(), bones[i].e_theta())
                                 for i in range(self.index)]))

    def tendon_position(self, bones, muscle):
        return muscle.tendon_position(self, bones)

    def v_tendon(self, bones, muscle):  # velocity of the tendon linking those specific bone and muscle
        return v_sum(v_list_sum([scalar_mul(bones[i].r * bones[i].theta_dot(), bones[i].e_theta())
                                 for i in range(self.index)]),
                     scalar_mul(self.theta_dot() * muscle.origin_to_tendon_length(self), self.e_theta()))

    def F_muscle(self, bones, muscle, effort):  # force exerted by a muscle on this bone
        u = v_sub(muscle.tendon_position(bones, muscle.other_bone(self)), muscle.tendon_position(bones, self))
        u = scalar_mul(1 / norm(u), u)  # unit vector
        return scalar_mul(effort * muscle.max_force, u)

    def F_tot_muscle(self, bones, efforts):  # add up the forces exerted by the muscles on this bone
        return v_list_sum([self.F_muscle(bones, muscle, efforts[muscle.index]) for muscle in self.muscles])

    def C_muscle(self, bones, muscle, effort):  # torque exerted by a muscle on this bone
        OM = v_sub(muscle.tendon_position(bones, self), self.G(bones))
        F = self.F_muscle(bones, muscle, effort)
        return OM[0] * F[1] - OM[1] * F[0]

    def C_tot_muscle(self, bones, efforts):  # add up the torque exerted by the muscles on this bone
        return sum([self.C_muscle(bones, muscle, efforts[muscle.index]) for muscle in self.muscles])


class Muscle:
    def __init__(self, index, bone0, bone1, relative_start, relative_end, max_force, color):
        self.index = index
        self.bone0 = bone0
        self.bone1 = bone1
        self.relative_0 = relative_start
        self.relative_1 = relative_end
        self.max_force = max_force
        self.color = color

    def origin(self, bones):
        return v_sum(self.bone0.origin(bones), change_basis(self.bone0.relative_to_absolute_matrix(), self.relative_0))

    def end(self, bones):
        return v_sum(self.bone1.origin(bones), change_basis(self.bone1.relative_to_absolute_matrix(), self.relative_1))

    def other_bone(self, bone):
        return self.bone1 if bone == self.bone0 else self.bone0

    def tendon_position(self, bones, bone):
        return v_sum(bone.origin(bones),
                     change_basis(bone.relative_to_absolute_matrix(), self.relative_tendon_position(bone)))

    def relative_tendon_position(self, bone):
        if bone == self.bone0:
            return self.relative_0
        else:
            return self.relative_1

    def origin_to_tendon_length(self, bone):
        return norm(self.relative_tendon_position(bone))

