#!/bin/bash
 
#PBS -l ncpus=48
#PBS -l mem=190GB
#PBS -l jobfs=1GB
#PBS -q normal
#PBS -P tq84 
#PBS -l walltime=12:00:00
#PBS -l storage=gdata/my80+scratch/my80+scratch/tq84+gdata/up99
#PBS -l wd


#module load python3/3.10.4
#source /scratch/tq84/kk9397/venvs/aurora/bin/activate
module use /g/data/up99/modulefiles 
module load NCI-geophys/23.11.dev
cd ~/software/irismt/aurora/aurora/test_utils/musgraves/
#python3 test_hpc.py --use_pandarallel=True $PBS_NCPUS > /scratch/tq84/$USER/job_logs/$PBS_JOBID.log
python3 test_hpc.py --use_pandarallel=True $PBS_NCPUS > /scratch/tq84/$USER/job_logs/$PBS_JOBID.log
