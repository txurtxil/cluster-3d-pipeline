#!/bin/bash
# launch_stress.sh — ejecutar EN rpi5
mkdir -p ~/recon3d/iterations/stress_test_01
nohup ~/pipeline3d/stress_mission.sh > ~/recon3d/iterations/stress_test_01/launcher.log 2>&1 &
echo "STRESS_PID $!"
