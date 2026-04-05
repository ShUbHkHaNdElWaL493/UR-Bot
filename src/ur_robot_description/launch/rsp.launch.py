from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def launch_setup(context):

    description_file = LaunchConfiguration("description_file")
    mode = LaunchConfiguration("mode")
    cobotizur_type = LaunchConfiguration("cobotizur_type")
    robot_ip = LaunchConfiguration("robot_ip")
    simulation_controllers = LaunchConfiguration("simulation_controllers")

    robot_description = Command([
        PathJoinSubstitution([FindExecutable(name = "xacro")]),
        " ",
        description_file,
        " ",
        "mode:=",
        mode,
        " ",
        "cobotizur_type:=",
        cobotizur_type,
        " ",
        "robot_ip:=",
        robot_ip,
        " ",
        "simulation_controllers:=",
        simulation_controllers
    ])

    robot_state_publisher_node = None

    if mode.perform(context) == "gz":
        robot_state_publisher_node = Node(
            package = "robot_state_publisher",
            executable = "robot_state_publisher",
            output = "both",
            parameters = [{
                "use_sim_time" : True,
                "robot_description" : robot_description
            }]
        )

    if mode.perform(context) == "hw":
        robot_state_publisher_node = Node(
            package = "robot_state_publisher",
            executable = "robot_state_publisher",
            output = "both",
            parameters = [{
                "use_sim_time" : False,
                "robot_description" : robot_description
            }]
        )
    
    return [robot_state_publisher_node]

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "description_file",
            default_value = PathJoinSubstitution([FindPackageShare("cobotizur_description"), "models", "robot.urdf.xacro"]),
            description = "URDF/XACRO description file (absolute path) with the robot."
        ),
        DeclareLaunchArgument(
            "mode",
            default_value = "hw",
            description = "Robot mode.",
            choices = [
                "gz",
                "hw"
            ]
        ),
        DeclareLaunchArgument(
            "cobotizur_type",
            default_value = "CT10",
            description = "Type/series of used cobotizur.",
            choices = [
                "CT10",
                "CF20"
            ]
        ),
        DeclareLaunchArgument(
            "robot_ip",
            default_value = "0.0.0.0",
            description = "IP address by which the robot can be reached."
        ),
        DeclareLaunchArgument(
            "simulation_controllers",
            default_value = '""',
            description = "Absolute path to YAML file with the controllers configuration."
        ),
        OpaqueFunction(function = launch_setup)
    ])