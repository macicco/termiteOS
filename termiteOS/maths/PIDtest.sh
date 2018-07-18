#!/bin/sh
./hPID.py >ivPID.dat
gnuplot << EOF
h=1200
set term png size h*4/3,h
set output "ivPID.png"
set key autotitle columnhead
set y2tics
set autoscale y2
set title "RA Axis"
plot "ivPID.dat" u 1:2 w lines, "ivPID.dat" u 1:3 w lines lw 2
EOF
eog ivPID.png
