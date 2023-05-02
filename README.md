# Automated-ILP-Scheduler

Takes an edgelist graph represented from a DFG and automatically generates the schedule using ILP solver GLPK and produces the Quality-of-Results. Supports ML-RC, MR-LC, or both using Pareto-optimal analysis.

## Documentation

### Setup 
* Use a Linux distribution
* Install Git and clone this repo:
`sudo apt update; sudo apt install git`
`git clone https://github.com/ElmirDzaka/Automated-ILP-Scheduler.git`
* Install Python and the library 'networkx':
`sudo apt install python3`
`pip install networkx`
* Install GLPK (in the same directory as this repo)
    * Download GLPK source and unzip the file:
    `wget http://ftp.gnu.org/gnu/glpk/glpk-4.35.tar.gz; tar -zxvf glpk-4.35.tar.gz`
    * Install libraries for compilation:
    `sudo apt-get install build-essential`
    * Enter the unzipped folder and prepare for compilation:
    `cd glpk-4.35; ./configure`
    * Compile and install GLPK to your system
    `make`
    * Verify your installation and run an example. If succeeds, you should see the same results shown in Figure 1.
    `cd examples; ./glpsol --cpxlp plan.lp`
    ![Figure 1: GLPK example of solving **plan.lp**](fig_1.png)

### How to Use
* Or just run the given shell scripts to use the supplied graph *test.edgelist* ...: *run_ml-rc.sh*, *run_mr-lc.sh* *run_both.sh*

## Future Features
* Generalize edgelist.py to take user input and generate custom DFGs
* Create timing benchmarks for different sized DFGs

## Author

Developed by [Elmir Dzaka](https://www.linkedin.com/in/elmir-dzaka-256b5b182/) and [Kidus Yohannes](https://kidusyohannes.me/)

## Version History

Started development on 04/03/2023

### Beta 

* 0.1 - 04/28/2023
    * Initial Release
    * MR-LC functionality implemented

## Resources

* Professor Cunxi Yu’s class slides
