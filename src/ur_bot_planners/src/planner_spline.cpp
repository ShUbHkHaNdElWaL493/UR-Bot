/*
    Shubh Khandelwal
*/

#include <iostream>
#include <ur_rtde/rtde_control_interface.h>
#include <ur_rtde/rtde_io_interface.h>
#include <ur_rtde/rtde_receive_interface.h>
#include <vector>

using namespace ur_rtde;

int main()
{

    std::string robot_ip = "192.168.56.101";

    try
    {

        std::cout << "Connecting to robot at " << robot_ip << "..." << std::endl;
        
        RTDEControlInterface control_interface(robot_ip);
        RTDEIOInterface io_interface(robot_ip);
        RTDEReceiveInterface receive_interface(robot_ip);

        return 0;

    } catch (const std::exception& e)
    {
        std::cerr << "RTDE Error: " << e.what() << std::endl;
        return 1;
    }

}