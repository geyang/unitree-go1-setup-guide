/*****************************************************************
 Copyright (c) 2020, Unitree Robotics.Co.Ltd. All rights reserved.
******************************************************************/

#include "unitree_legged_sdk/unitree_legged_sdk.h"
#include <math.h>
#include <iostream>
#include <stdio.h>
#include <stdint.h>


#include <lcm/lcm-cpp.hpp>
#include "pd_tau_targets_lcmt.hpp"
#include "leg_control_data_lcmt.hpp"
#include "state_estimator_lcmt.hpp"

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


    Safety safe;
    UDP udp;
    LowCmd cmd = {0};
    LowState state = {0};
    float qInit[12]={0};
    float qDes[12]={0};
    float Kp[3] = {0};  
    float Kd[3] = {0};
    double time_consume = 0;
    int rate_count = 0;
    int sin_count = 0;
    int motiontime = 0;
    float dt = 0.002;     // 0.001~0.01

    bool _terminalFlag = false; 
    int _policyRecieved = 0;
    float _tau_ff[12] = {0};
    float _des_jpos[12] = {0};
    float _des_jvel[12] = {0};
    float _Kp_joint[12] = {0};
    float _Kd_joint[12] = {0};

    lcm::LCM _pdLCM;

    void LCMCtrlThread() { 
      while (!_terminalFlag) {
        //std::cout << "handling\n";
        _pdLCM.handle();
      }
    }

    void setup();

    void handleActionLCM(const lcm::ReceiveBuffer *rbuf, const std::string &chan, const pd_tau_targets_lcmt *msg);
};

void Custom::UDPRecv()
{  
    udp.Recv();
}

void Custom::UDPSend()
{  
    udp.Send();
}

void Custom::setup(){
  _terminalFlag=false;
  _policyRecieved = 0;
  for(int leg=0; leg<4; leg++){
    for(int i=0; i<3; i++){
        _tau_ff[leg*3+i] = 0.;
        _des_jvel[leg*3+i] = 0.f;
        _Kp_joint[leg*3+i] = 40.f;
        _Kd_joint[leg*3+i] = 1.f;
    }
  }
  _des_jpos[0] = -0.1;
  _des_jpos[1] = 0.8;
  _des_jpos[2] = -1.5;
  _des_jpos[3] = 0.1;
  _des_jpos[4] = 0.8;
  _des_jpos[5] = -1.5;
  _des_jpos[6] = -0.1;
  _des_jpos[7] = 1.0;
  _des_jpos[8] = -1.5;
  _des_jpos[9] = 0.1;
  _des_jpos[10] = 1.0;
  _des_jpos[11] = -1.5;


}

void Custom::handleActionLCM(const lcm::ReceiveBuffer *rbuf,
    const std::string &chan,
    const pd_tau_targets_lcmt *msg){
    
    (void)rbuf;
    (void)chan;

    for(int i = 0; i < 12; i++){
        _des_jpos[i] = msg->q_des[i];
        //std::cout << i << " q " << msg->q_des[i] << "\n";
        _des_jvel[i] = msg->qd_des[i];
        _tau_ff[i] = msg->tau_ff[i];
      }
      for(int i = 0; i < 3; i++){
        _Kp_joint[i] = msg->kp[i];
        _Kd_joint[i] = msg->kd[i];
      }



      //printf("Successfully read action\n");

      _policyRecieved = 1;

}



double jointLinearInterpolation(double initPos, double targetPos, double rate)
{
    double p;
    rate = std::min(std::max(rate, 0.0), 1.0);
    p = initPos*(1-rate) + targetPos*rate;
    return p;
}

void Custom::RobotControl() 
{
    motiontime++;
    udp.GetRecv(state);
    // printf("%d  %f\n", motiontime, state.motorState[FR_2].q);
    printf("%d  %f\n", motiontime, state.imu.quaternion[2]);

    
    // act based on most recent command
    cmd.motorCmd[FR_0].tau = 0.0f;
    cmd.motorCmd[FL_0].tau = 0.0f;
    cmd.motorCmd[RR_0].tau = 0.0f;
    cmd.motorCmd[RL_0].tau = 0.0f;

    if(motiontime >= 0){
        //get initial position
        if(motiontime >= 0 and motiontime < 10){
            qInit[0] = state.motorState[FR_0].q;
            qInit[1] = state.motorState[FR_1].q;
            qInit[2] = state.motorState[FR_2].q;
            qInit[3] = state.motorState[FR_0].q;
            qInit[4] = state.motorState[FR_1].q;
            qInit[5] = state.motorState[FR_2].q;
            qInit[6] = state.motorState[FR_0].q;
            qInit[7] = state.motorState[FR_1].q;
            qInit[8] = state.motorState[FR_2].q;
            qInit[9] = state.motorState[FR_0].q;
            qInit[10] = state.motorState[FR_1].q;
            qInit[11] = state.motorState[FR_2].q;

            for(int i = 0; i < 12; i++){
                if(abs(_des_jpos[i] - qInit[i]) > 0.1){
                    printf("ERROR: Please initialize robot from standing position!");
                    return;
                }
            }
        }
    }

    for(int i = 0; i < 12; i++){
        cmd.motorCmd[i].q = _des_jpos[i];
        cmd.motorCmd[i].dq = _des_jvel[i];
        cmd.motorCmd[i].Kp = _Kp_joint[i];
        cmd.motorCmd[i].Kd = _Kd_joint[i];
        cmd.motorCmd[i].tau = 0.0f;
    }


    // // gravity compensation
    // cmd.motorCmd[FR_0].tau = -0.65f;
    // cmd.motorCmd[FL_0].tau = +0.65f;
    // cmd.motorCmd[RR_0].tau = -0.65f;
    // cmd.motorCmd[RL_0].tau = +0.65f;

    // // if( motiontime >= 100){
    // if( motiontime >= 0){
    //     // first, get record initial position
    //     // if( motiontime >= 100 && motiontime < 500){
    //     if( motiontime >= 0 && motiontime < 10){
    //         qInit[0] = state.motorState[FR_0].q;
    //         qInit[1] = state.motorState[FR_1].q;
    //         qInit[2] = state.motorState[FR_2].q;
    //     }
    //     // second, move to the origin point of a sine movement with Kp Kd
    //     // if( motiontime >= 500 && motiontime < 1500){
    //     if( motiontime >= 10 && motiontime < 400){
    //         rate_count++;
    //         double rate = rate_count/200.0;                       // needs count to 200
    //         Kp[0] = 5.0; Kp[1] = 5.0; Kp[2] = 5.0; 
    //         Kd[0] = 1.0; Kd[1] = 1.0; Kd[2] = 1.0;
            
    //         qDes[0] = jointLinearInterpolation(qInit[0], sin_mid_q[0], rate);
    //         qDes[1] = jointLinearInterpolation(qInit[1], sin_mid_q[1], rate);
    //         qDes[2] = jointLinearInterpolation(qInit[2], sin_mid_q[2], rate);
    //     }
    //     double sin_joint1, sin_joint2;
    //     // last, do sine wave
    //     if( motiontime >= 400){
    //         sin_count++;
    //         sin_joint1 = 0.6 * sin(3*M_PI*sin_count/1000.0);
    //         sin_joint2 = -0.6 * sin(1.8*M_PI*sin_count/1000.0);
    //         qDes[0] = sin_mid_q[0];
    //         qDes[1] = sin_mid_q[1];
    //         qDes[2] = sin_mid_q[2] + sin_joint2;
    //         // qDes[2] = sin_mid_q[2];
    //     }

    //     cmd.motorCmd[FR_0].q = qDes[0];
    //     cmd.motorCmd[FR_0].dq = 0;
    //     cmd.motorCmd[FR_0].Kp = Kp[0];
    //     cmd.motorCmd[FR_0].Kd = Kd[0];
    //     cmd.motorCmd[FR_0].tau = -0.65f;

    //     cmd.motorCmd[FR_1].q = qDes[1];
    //     cmd.motorCmd[FR_1].dq = 0;
    //     cmd.motorCmd[FR_1].Kp = Kp[1];
    //     cmd.motorCmd[FR_1].Kd = Kd[1];
    //     cmd.motorCmd[FR_1].tau = 0.0f;

    //     cmd.motorCmd[FR_2].q =  qDes[2];
    //     cmd.motorCmd[FR_2].dq = 0;
    //     cmd.motorCmd[FR_2].Kp = Kp[2];
    //     cmd.motorCmd[FR_2].Kd = Kd[2];
    //     cmd.motorCmd[FR_2].tau = 0.0f;

    // }

    if(motiontime > 10){
        safe.PositionLimit(cmd);
        int res1 = safe.PowerProtect(cmd, state, 1);
        // You can uncomment it for position protection
        // int res2 = safe.PositionProtect(cmd, state, 0.087);
        if(res1 < 0) exit(-1);
    }

    udp.SetSend(cmd);

}


int main(void)
{
    std::cout << "Communication level is set to LOW-level." << std::endl
              << "WARNING: Make sure the robot is hung up." << std::endl
              << "Press Enter to continue..." << std::endl;
    std::cin.ignore();
    
    Custom custom(LOWLEVEL);
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
