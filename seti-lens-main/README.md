## Installation

0. Make sure you have access to ACI:
   * https://www.icds.psu.edu/computing-services/account-setup/ 

1. Set up an SSH key for GitHub (if you haven't already):
   * Follow the Linux directions [here](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)

2. Clone seti-lens: 
```bash
cd ~/work/
git clone git@github.com:palumbom/seti-lens.git
```

3. Install (most) dependencies into a new environment:
```bash
cd ~/work/seti-lens/
module load python/3.6.3-anaconda5.0.1
conda env create -f seti.yml
source activate seti
conda install numba
```

4. Install blimpy:
```bash
cd ~/work/
git clone git@github.com:UCBerkeleySETI/blimpy.git
pip install ./blimpy/
```

5. Install Sofia Sheikh's modified turbo_seti:
```bash
cd ~/work/
git clone git@github.com:palumbom/turbo_seti.git
pip install ./turbo_seti/
```

Remember to type ```source activate seti``` at each new session to ensure that you are in the correct environment. 
