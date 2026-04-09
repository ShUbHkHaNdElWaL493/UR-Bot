from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import Command, EnvironmentVariable, FindExecutable, LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def launch_setup(context):

    mode = LaunchConfiguration("mode")
    robot_ip = LaunchConfiguration("robot_ip")
    controllers = LaunchConfiguration("controllers")

    robot_description = Command([
        PathJoinSubstitution([FindExecutable(name = "xacro")]),
        " ",
        PathJoinSubstitution([FindPackageShare("ur_bot_description"), "models", "robot.urdf.xacro"]),
        " ",
        "mode:=",
        mode,
        " ",
        "ur_type:=",
        PythonExpression(["'", EnvironmentVariable("UR_MODEL"), "'.lower()"]),
        " ",
        "robot_ip:=",
        robot_ip,
        " ",
        "simulation_controllers:=",
        controllers
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
            "mode",
            default_value = "hw",
            description = "Robot mode.",
            choices = [
                "gz",
                "hw"
            ]
        ),
        DeclareLaunchArgument(
            "robot_ip",
            default_value = "0.0.0.0",
            description = "IP address by which the robot can be reached."
        ),
        DeclareLaunchArgument(
            "controllers",
            default_value = '""',
            description = "Absolute path to YAML file with the controllers configuration."
        ),
        OpaqueFunction(function = launch_setup)
    ])