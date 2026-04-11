#!/usr/bin/env python3

from cobotizur_description.srv import Case
from matplotlib import pyplot as plt
import numpy as np
import rclpy
from rclpy.node import Node
import rtde_control
import rtde_io
import rtde_receive

class SplineGenerator:

    def __init__(self, basis_matrix: np.array, resolution: int, epsilon: float):
        self.basis_matrix = basis_matrix
        self.resolution = resolution
        self.epsilon = epsilon

    def _interpolate(self, p0, p1, p2, p3):
        a = self.basis_matrix @ np.array([p0, p1, p2, p3])
        t = np.linspace(0, 1, self.resolution)
        pos = np.array([np.ones_like(t), t, t ** 2, t ** 3]).T @ a
        vel = np.array([np.zeros_like(t), np.ones_like(t), 2 * t, 3 * t ** 2]).T @ a
        acc = np.array([np.zeros_like(t), np.zeros_like(t), 2 * np.ones_like(t), 6 * t]).T @ a
        jrk = np.array([np.zeros_like(t), np.zeros_like(t), np.zeros_like(t), 6 * np.ones_like(t)]).T @ a
        return pos, vel, acc, jrk
    
    def get_path(self, waypoints: list):

        clean_waypoints = [waypoints[0], waypoints[0]]
        for i in range(1, len(waypoints)):
            if np.linalg.norm(waypoints[i] - waypoints[i - 1]) > self.epsilon:
                clean_waypoints.append(waypoints[i])
        clean_waypoints.append(clean_waypoints[-1])

        P = []
        V = []
        A = []
        J = []
        for i in range(len(clean_waypoints) - 3):

            p0 = clean_waypoints[i]
            p1 = clean_waypoints[i + 1]
            p2 = clean_waypoints[i + 2]
            p3 = clean_waypoints[i + 3]
            pos, vel, acc, jrk = self._interpolate(p0, p1, p2, p3)

            P.append(pos)
            V.append(vel)
            A.append(acc)
            J.append(jrk)

        P = np.concatenate(P)
        V = np.concatenate(V)
        A = np.concatenate(A)
        J = np.concatenate(J)
        return P, V, A, J

class CatmullRomSplineGenerator(SplineGenerator):

    def __init__(self, resolution, epsilon = 1e-6):
        basis_matrix = 1 / 2 * np.array([
            [0, 2, 0, 0],
            [-1, 0, 1, 0],
            [2, -5, 4, -1],
            [-1, 3, -3, 1]
        ])
        super().__init__(basis_matrix, resolution = resolution, epsilon = epsilon)
    
class BSplineGenerator(SplineGenerator):

    def __init__(self, resolution, epsilon = 1e-6):
        basis_matrix = 1 / 6 * np.array([
            [1, 4, 1, 0],
            [-3, 0, 3, 0],
            [3, -6, 3, 0],
            [-1, 3, -3, 1],
        ])
        super().__init__(basis_matrix, resolution = resolution, epsilon = epsilon)

class URInterface:

    def __init__(self, frequency, robot_ip = "0.0.0.0"):
        self.frequency = frequency
        self.rtde_c = rtde_control.RTDEControlInterface(robot_ip)
        self.rtde_i = rtde_io.RTDEIOInterface(robot_ip)
        self.rtde_r = rtde_receive.RTDEReceiveInterface(robot_ip)

    def _discretize(self, path):
        pass

    def _receive_jacobian(self):
        pass

    def _send_joint_speeds(self, joint_speeds):
        pass

    def send_path(self, path):
        velocity = self._discretize(path)
        joint_speeds = self._receive_jacobian() * velocity
        self._send_joint_speeds(joint_speeds)

class SplinePlanner(Node):

    def __init__(self):

        super().__init__("planner_node", allow_undeclared_parameters = True, automatically_declare_parameters_from_overrides = True)

        self.conveyor_z = self.get_parameter("conveyor_z").get_parameter_value().double_value
        self.case_length = self.get_parameter("case_length").get_parameter_value().double_value
        self.case_width = self.get_parameter("case_width").get_parameter_value().double_value
        self.case_height = self.get_parameter("case_height").get_parameter_value().double_value

        self.crs = CatmullRomSplineGenerator(50)
        self.bs = BSplineGenerator(50)

        self.goals = []

        self.homej = [
            -1.5708,
            -1.5708,
            -1.5708,
            -1.5708,
            1.5708,
            0
        ]
        self.home = {
            "position" : np.array([
                0,
                1 + self.case_width / 2,
                self.conveyor_z + self.case_height + 0.5
            ]),
            "orientation" : False
        }
        self.pickup = {
            "position" : np.array([
                0,
                1 + self.case_width / 2,
                self.conveyor_z + self.case_height
            ]),
            "orientation" : False
        }
        
        self.planner_service = self.create_service(Case, "/planner", self.planner_callback)

    def planner_callback(self, request: Case.Request, response: Case.Response):
        if request.execute:
            self.execute()
            response.success = True
            return response
        goal = {
            "position" : np.array(request.position),
            "orientation" : request.orientation
        }
        self.goals.append(goal)
        response.success = True
        return response

    def execute(self):

        pre_pickup = self.pickup["position"]
        pre_pickup[2] += 0.1
        self.waypoints = [self.home["position"]]
        for i in range(len(self.goals)):
            place = self.goals[i]["position"]
            pre_place = place
            pre_place[2] += 0.1
            top = pre_pickup + pre_place / 2
            top[2] += 0.6
            self.waypoints.append(pre_pickup)
            self.waypoints.append(self.pickup["position"])
            self.waypoints.append(pre_pickup)
            self.waypoints.append(top)
            self.waypoints.append(pre_place)
            self.waypoints.append(place)
            self.waypoints.append(pre_place)
            self.waypoints.append(top)
        self.waypoints.append(self.home["position"])
        
        pos, _, _, _ = self.crs.get_path(self.waypoints)
        pos, vel, acc, jrk = self.bs.get_path(pos)
        pos_x = [pos[i][0] for i in range(len(pos))]
        pos_y = [pos[i][1] for i in range(len(pos))]
        pos_z = [pos[i][2] for i in range(len(pos))]
        vel_x = [vel[i][0] for i in range(len(vel))]
        vel_y = [vel[i][1] for i in range(len(vel))]
        vel_z = [vel[i][2] for i in range(len(vel))]
        acc_x = [acc[i][0] for i in range(len(acc))]
        acc_y = [acc[i][1] for i in range(len(acc))]
        acc_z = [acc[i][2] for i in range(len(acc))]
        jrk_x = [jrk[i][0] for i in range(len(jrk))]
        jrk_y = [jrk[i][1] for i in range(len(jrk))]
        jrk_z = [jrk[i][2] for i in range(len(jrk))]

        fig, axs = plt.subplots(2, 2, figsize = (12, 10), subplot_kw = {"projection" : "3d"})
        axs[0, 0].plot(pos_x, pos_y, pos_z, color = "red")
        axs[0, 0].set_title("Position")
        axs[0, 1].plot(vel_x, vel_y, vel_z, color = "blue")
        axs[0, 1].set_title("Velocity")
        axs[1, 0].plot(acc_x, acc_y, acc_z, color = "green")
        axs[1, 0].set_title("Accelaration")
        axs[1, 1].plot(jrk_x, jrk_y, jrk_z, color = "orange")
        axs[1, 1].set_title("Jerk")

        plt.tight_layout()
        plt.show()

def main():
    rclpy.init()
    rclpy.spin(SplinePlanner())
    rclpy.shutdown()

if __name__ == "__main__":
    main()
    # x = [
    #     np.array([0]),
    #     np.array([3]),
    #     np.array([2]),
    #     np.array([6]),
    #     np.array([8]),
    #     np.array([7]),
    #     np.array([1]),
    #     np.array([9]),
    #     np.array([0])
    # ]
    # crs = CatmullRomSplineGenerator()
    # bs = BSplineGenerator()
    # pos, _, _, _ = crs.get_path(x)
    # pos, vel, acc, jrk = bs.get_path(pos)

    # pos_x = [pos[i][0] for i in range(len(pos))]
    # vel_x = [vel[i][0] for i in range(len(vel))]
    # acc_x = [acc[i][0] for i in range(len(acc))]
    # jrk_x = [jrk[i][0] for i in range(len(jrk))]

    # fig, axs = plt.subplots(4, 1, figsize = (12, 10))
    # axs[0].plot(pos_x, color = "red")
    # axs[0].set_title("Position")
    # axs[1].plot(vel_x, color = "blue")
    # axs[1].set_title("Velocity")
    # axs[2].plot(acc_x, color = "green")
    # axs[2].set_title("Accelaration")
    # axs[3].plot(jrk_x, color = "orange")
    # axs[3].set_title("Jerk")

    # plt.tight_layout()
    # plt.show()