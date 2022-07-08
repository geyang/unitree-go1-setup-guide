/************************************************************************
Copyright (c) 2020, Unitree Robotics.Co.Ltd. All rights reserved.
Use of this source code is governed by the MPL-2.0 license, see LICENSE.
************************************************************************/

#ifndef _UNITREE_LEGGED_LCM_SERVER_
#define _UNITREE_LEGGED_LCM_SERVER_

#include "comm.h"
#include "unitree_legged_sdk/unitree_legged_sdk.h"
#include <iostream>
#include "state_estimator_lcmt.hpp"
#include "leg_control_data_lcmt.hpp"

namespace UNITREE_LEGGED_SDK
{
// Low command Lcm Server
class Lcm_Server_Low
{
public:
    Lcm_Server_Low() : udp(LOWLEVEL), mylcm(LOWLEVEL){
        udp.InitCmdData(cmd);
    }
    void UDPRecv(){
        udp.Recv();
    }
    void UDPSend(){
        udp.Send();
    }
    void LCMRecv();
    void RobotControl();

    UDP udp;
    LCM mylcm;
    LowCmd cmd = {0};
    LowState state = {0};
    state_estimator_lcmt body_state_simple = {0};
    leg_control_data_lcmt joint_state_simple = {0};

    lcm::LCM _simpleLCM;
};
//void Lcm_Server_Low::init()
//{
//    _simpleLCM.subscribe("LCM_Low_Cmd_Simple", )
//}
void Lcm_Server_Low::LCMRecv()
{
    if(mylcm.lowCmdLCMHandler.isrunning){
        pthread_mutex_lock(&mylcm.lowCmdLCMHandler.countMut);
        mylcm.lowCmdLCMHandler.counter++;
        if(mylcm.lowCmdLCMHandler.counter > 10){
            printf("Error! LCM Time out.\n");
            exit(-1);              // can be commented out
        }
        pthread_mutex_unlock(&mylcm.lowCmdLCMHandler.countMut);
    }
    mylcm.Recv();
}
void Lcm_Server_Low::RobotControl()
{
    udp.GetRecv(state);
    printf("%f\n", state.imu.quaternion[2]);

    // transcribe simple state
    for(int i = 0; i < 12; i++){
        joint_state_simple.q[i] = state.motorState[i].q;
        joint_state_simple.qd[i] = state.motorState[i].dq;
    }
    for(int i = 0; i < 4; i++){
        body_state_simple.quat[i] = state.imu.quaternion[i];
    }
    for(int i = 0; i < 3; i++){
        body_state_simple.rpy[i] = state.imu.rpy[i];
        body_state_simple.aBody[i] = state.imu.accelerometer[i];
        body_state_simple.omegaBody[i] = state.imu.gyroscope[i];
    }
    std::cout << "q0 " <<  joint_state_simple.q[0] << "\n";
    std::cout << "roll " <<  body_state_simple.rpy[0] << "\n";
    printf("%f\n", state.imu.quaternion[2]);

    mylcm.Send(state);
    _simpleLCM.publish("body_state_simple", &body_state_simple);
    _simpleLCM.publish("joint_state_simple", &joint_state_simple);

    mylcm.Get(cmd);
    //_simpleLCM.handle();
    // TODO: transcribe simple cmd


    udp.SetSend(cmd);
}



// High command Lcm Server
class Lcm_Server_High
{
public:
    Lcm_Server_High(): udp(8090, "192.168.123.161", 8082, sizeof(HighCmd), sizeof(HighState)), mylcm(HIGHLEVEL){
        udp.InitCmdData(cmd);
    }
    void UDPRecv(){
        udp.Recv();
    }
    void UDPSend(){
        udp.Send();
    }
    void LCMRecv();
    void RobotControl();

    UDP udp;
    LCM mylcm;
    HighCmd cmd = {0};
    HighState state = {0};
};

void Lcm_Server_High::LCMRecv()
{
    if(mylcm.highCmdLCMHandler.isrunning){
        pthread_mutex_lock(&mylcm.highCmdLCMHandler.countMut);
        mylcm.highCmdLCMHandler.counter++;
        if(mylcm.highCmdLCMHandler.counter > 10){
            printf("Error! LCM Time out.\n");
            exit(-1);              // can be commented out
        }
        pthread_mutex_unlock(&mylcm.highCmdLCMHandler.countMut);
    }
    mylcm.Recv();
}

void Lcm_Server_High::RobotControl()
{
    udp.GetRecv(state);
    mylcm.Send(state);
    mylcm.Get(cmd);
    udp.SetSend(cmd);
}




}
#endif