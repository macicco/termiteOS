#!/bin/sh
./trapeze.py >trapeze.dat
gnuplot << EOF
h=1200
set term png size h*4/3,h
set output "trapeze.png"
set key autotitle columnhead
set y2tics
set autoscale y2
set  ytics 
set  xtics 
set grid
set zeroaxis
set title "Trapeze speed controller"
plot "trapeze.dat" u 1:2  title "SetPoint" lw 2 with steps, \
     "trapeze.dat" u 1:3  title "Actual" lw 2 with steps, \
     "trapeze.dat" u 1:4  title "Speed" lw 2 with steps
EOF
eog trapeze.png
