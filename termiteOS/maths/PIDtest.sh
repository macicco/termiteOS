#!/bin/sh
./hPID.py >hPID.dat
gnuplot << EOF
h=1200
set term png size h*4/3,h
set output "hPID.png"
set key autotitle columnhead
set y2tics
set autoscale y2
set title "RA Axis"
plot "hPID.dat" u 1:2 w lines, "hPID.dat" u 1:3 w lines lw 2
EOF
eog hPID.png
