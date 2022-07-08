/*****************************************************************
 Copyright (c) 2020, Unitree Robotics.Co.Ltd. All rights reserved.
******************************************************************/

#include "unitree_legged_sdk/unitree_legged_sdk.h"
#include "unitree_legged_sdk/unitree_joystick.h"
#include <math.h>
#include <iostream>
#include <stdio.h>
#include <stdint.h>
#include <thread>
#include <lcm/lcm-cpp.hpp>
#include "state_estimator_lcmt.hpp"
#include "leg_control_data_lcmt.hpp"
#include "pd_tau_targets_lcmt.hpp"
#include "rc_command_lcmt.hpp"

using namespace std;
using namespace UNITREE_LEGGED_SDK;

class Custom
{
public:
    Custom(uint8_t level): safe(LeggedType::Go1), udp(level) {
        udp.InitCmdData(cmd);
    }
    void UDPRecv();
    void UDPSend();
    void RobotControl();
    void init();
    void handleActionLCM(const lcm::ReceiveBuffer *rbuf, const std::string & chan, const pd_tau_targets_lcmt * msg);
    void _simpleLCMThread();

    Safety safe;
    UDP udp;
    LowCmd cmd = {0};
    LowState state = {0};
    float qInit[3]={0};
    float qDes[3]={0};
    float sin_mid_q[3] = {0.0, 1.2, -2.0};
    float Kp[3] = {0};
    float Kd[3] = {0};
    double time_consume = 0;
    int rate_count = 0;
    int sin_count = 0;
    int motiontime = 0;
    float dt = 0.002;     // 0.001~0.01

    lcm::LCM _simpleLCM;
    std::thread _simple_LCM_thread;
    bool _firstCommandReceived;
    bool _firstRun;
    state_estimator_lcmt body_state_simple = {0};
    leg_control_data_lcmt joint_state_simple = {0};
    pd_tau_targets_lcmt joint_command_simple = {0};
    rc_command_lcmt rc_command = {0};

    xRockerBtnDataStruct _keyData;
    int mode = 0;

};

void Custom::init()
{
    _simpleLCM.subscribe("pd_plustau_targets", &Custom::handleActionLCM, this);
    _simple_LCM_thread = std::thread(&Custom::_simpleLCMThread, this);

    _firstCommandReceived = false;
    _firstRun = true;

    // set nominal pose

    for(int i = 0; i < 12; i++){
        joint_command_simple.qd_des[i] = 0;
        joint_command_simple.tau_ff[i] = 0;
        joint_command_simple.kp[i] = 20.;
        joint_command_simple.kd[i] = 0.5;
    }

    joint_command_simple.q_des[0] = 0.1;
    joint_command_simple.q_des[1] = 0.8;
    joint_command_simple.q_des[2] = -1.5;
    joint_command_simple.q_des[3] = -0.1;
    joint_command_simple.q_des[4] = 0.8;
    joint_command_simple.q_des[5] = -1.5;
    joint_command_simple.q_des[6] = 0.1;
    joint_command_simple.q_des[7] = 1.0;
    joint_command_simple.q_des[8] = -1.5;
    joint_command_simple.q_des[9] = -0.1;
    joint_command_simple.q_des[10] = 0.8;
    joint_command_simple.q_des[11] = -1.5;

    printf("SET NOMINAL POSE");


}

void Custom::UDPRecv()
{
    udp.Recv();
}

void Custom::UDPSend()
{
    udp.Send();
}

double jointLinearInterpolation(double initPos, double targetPos, double rate)
{
    double p;
    rate = std::min(std::max(rate, 0.0), 1.0);
    p = initPos*(1-rate) + targetPos*rate;
    return p;
}

void Custom::handleActionLCM(const lcm::ReceiveBuffer *rbuf, const std::string & chan, const pd_tau_targets_lcmt * msg){
    (void) rbuf;
    (void) chan;

    joint_command_simple = *msg;
    _firstCommandReceived = true;

}

void Custom::_simpleLCMThread(){
    while(true){
        _simpleLCM.handle();
    }
}

void Custom::RobotControl()
{
    motiontime++;
    udp.GetRecv(state);
    // printf("%d  %f\n", motiontime, state.motorState[FR_2].q);
    // printf("%d  %f\n", motiontime, state.imu.quaternion[2]);

    memcpy(&_keyData, state.wirelessRemote, 40);

    rc_command.left_stick[0] = _keyData.lx;
    rc_command.left_stick[1] = _keyData.ly;
    rc_command.right_stick[0] = _keyData.rx;
    rc_command.right_stick[1] = _keyData.ry;
    rc_command.right_lower_right_switch = _keyData.btn.components.R2;
    rc_command.right_upper_switch = _keyData.btn.components.R1;
    rc_command.left_lower_left_switch = _keyData.btn.components.L2;
    rc_command.left_upper_switch = _keyData.btn.components.L1;


    if(_keyData.btn.components.A > 0){
        mode = 0;
    } else if(_keyData.btn.components.B > 0){
        mode = 1;
    }else if(_keyData.btn.components.X > 0){
        mode = 2;
    }else if(_keyData.btn.components.Y > 0){
        mode = 3;
    }else if(_keyData.btn.components.up > 0){
        mode = 4;
    }else if(_keyData.btn.components.right > 0){
        mode = 5;
    }else if(_keyData.btn.components.down > 0){
        mode = 6;
    }else if(_keyData.btn.components.left > 0){
        mode = 7;
    }

    rc_command.mode = mode;


    // publish state to LCM
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
    for(int i = 0; i < 4; i++){
        body_state_simple.contact_estimate[i] = state.footForce[i];
    }
//    for(int i = 0; i < 12; i++){
//        std::cout << " " <<  joint_state_simple.q[i];
//    }
//    std::cout << "\n";
//    std::cout << "roll " <<  body_state_simple.rpy[0] << "\n";
//    printf("%f\n", state.imu.quaternion[2]);

    _simpleLCM.publish("state_estimator_data", &body_state_simple);
    _simpleLCM.publish("leg_control_data", &joint_state_simple);
    _simpleLCM.publish("rc_command", &rc_command);

    //end lcm publish

    // verify received message
//    std::cout << "first command received: " << _firstCommandReceived << "\n";
//    if(_firstCommandReceived){
//        printf("joint position commanded:  %f\n", joint_command_simple.q_des[0]);
//    }
    if(_firstRun && joint_state_simple.q[0] != 0){
        for(int i = 0; i < 12; i++){
            joint_command_simple.q_des[i] = joint_state_simple.q[i];
        }
        _firstRun = false;
    }

//    std::cout << "command ";
//    for(int i = 0; i < 12; i++){
//        std::cout << " " <<  joint_command_simple.q_des[i];
//    }
//    std::cout << "\n";




    // gravity compensation
    //cmd.motorCmd[FR_0].tau = -0.65f;
    //cmd.motorCmd[FL_0].tau = +0.65f;
    //cmd.motorCmd[RR_0].tau = -0.65f;
    //cmd.motorCmd[RL_0].tau = +0.65f;

    // if( motiontime >= 100){
//    if( motiontime >= 0){
//        // first, get record initial position
//        // if( motiontime >= 100 && motiontime < 500){
//        if( motiontime >= 0 && motiontime < 10){
//            qInit[0] = state.motorState[FR_0].q;
//            qInit[1] = state.motorState[FR_1].q;
//            qInit[2] = state.motorState[FR_2].q;
//        }
//        // second, move to the origin point of a sine movement with Kp Kd
//        // if( motiontime >= 500 && motiontime < 1500){
//        if( motiontime >= 10 && motiontime < 400){
//            rate_count++;
//            double rate = rate_count/200.0;                       // needs count to 200
//            Kp[0] = 5.0; Kp[1] = 5.0; Kp[2] = 5.0;
//            Kd[0] = 1.0; Kd[1] = 1.0; Kd[2] = 1.0;
//
//            qDes[0] = jointLinearInterpolation(qInit[0], sin_mid_q[0], rate);
//            qDes[1] = jointLinearInterpolation(qInit[1], sin_mid_q[1], rate);
//            qDes[2] = jointLinearInterpolation(qInit[2], sin_mid_q[2], rate);
//        }
//        double sin_joint1, sin_joint2;
//        // last, do sine wave
//        if( motiontime >= 400){
//            sin_count++;
//            sin_joint1 = 0.6 * sin(3*M_PI*sin_count/1000.0);
//            sin_joint2 = -0.6 * sin(1.8*M_PI*sin_count/1000.0);
//            qDes[0] = sin_mid_q[0];
//            qDes[1] = sin_mid_q[1];
//            qDes[2] = sin_mid_q[2] + sin_joint2;
//            // qDes[2] = sin_mid_q[2];
//        }

    for(int i = 0; i < 12; i++){
        cmd.motorCmd[i].q = joint_command_simple.q_des[i];
        cmd.motorCmd[i].dq = joint_command_simple.qd_des[i];
        cmd.motorCmd[i].Kp = joint_command_simple.kp[i];
        cmd.motorCmd[i].Kd = joint_command_simple.kd[i];
        cmd.motorCmd[i].tau = joint_command_simple.tau_ff[i];
    }

//        cmd.motorCmd[FR_1].q = qDes[1];
//        cmd.motorCmd[FR_1].dq = 0;
//        cmd.motorCmd[FR_1].Kp = Kp[1];
//        cmd.motorCmd[FR_1].Kd = Kd[1];
//        cmd.motorCmd[FR_1].tau = 0.0f;
//
//        cmd.motorCmd[FR_2].q =  qDes[2];
//        cmd.motorCmd[FR_2].dq = 0;
//        cmd.motorCmd[FR_2].Kp = Kp[2];
//        cmd.motorCmd[FR_2].Kd = Kd[2];
//        cmd.motorCmd[FR_2].tau = 0.0f;

//    }

//    if(motiontime > 10){

    safe.PositionLimit(cmd);
    int res1 = safe.PowerProtect(cmd, state, 9);
    // std::cout << "power protection 8 \n";
    // You can uncomment it for position protection
    // int res2 = safe.PositionProtect(cmd, state, 0.087);
    // printf("%u\n", _keyData.btn.components.L2);
    // if(res1 < 0) exit(-1);

//    if(_keyData.btn.components.L2 > 0){
//        sleep(0.1);
//        //std::cout << "ESTOP\n";
//    } else if(res1 < 0){
//        std::cout << "ESTOP\n";
//        while(_keyData.btn.components.R2 == 0){
//            // wait for estop button press
//            sleep(0.1);
//            //
//            udp.GetRecv(state);
//            memcpy(&_keyData, state.wirelessRemote, 40);
//        }
//        std::cout << "END ESTOP\n";
//    }
//    else{
    udp.SetSend(cmd);
//    }

}


int main(void)
{
    std::cout << "Communication level is set to LOW-level." << std::endl
              << "WARNING: Make sure the robot is hung up." << std::endl
              << "Press Enter to continue..." << std::endl;
    std::cin.ignore();

    Custom custom(LOWLEVEL);
    custom.init();
    // InitEnvironment();
    LoopFunc loop_control("control_loop", custom.dt,    boost::bind(&Custom::RobotControl, &custom));
    LoopFunc loop_udpSend("udp_send",     custom.dt, 3, boost::bind(&Custom::UDPSend,      &custom));
    LoopFunc loop_udpRecv("udp_recv",     custom.dt, 3, boost::bind(&Custom::UDPRecv,      &custom));

    loop_udpSend.start();
    loop_udpRecv.start();
    loop_control.start();

    while(1){
        sleep(10);
    };

    return 0;
}
