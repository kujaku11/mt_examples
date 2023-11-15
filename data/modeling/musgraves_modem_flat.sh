#!/bin/bash
#PBS -N run_name
#PBS -q normal
#PBS -P tq84
#PBS -l walltime=1:00:00
#PBS -l ncpus=48
#PBS -l mem=190GB
#PBS -l jobfs=10GB
#PBS -l storage=gdata/nm05+scratch/nm05

module load ModEM-geophysics/2015.01

cd /mt_examples/data/modeling
mpirun -np 48 Mod3DMT_MPI -I NLCG musgraves_sm500.rho musgraves_z05_t02.dat control.inv control.fwd musgraves.cov > musgraves_flat.out