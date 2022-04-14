# Scripts for interacting with Webknossos.

1. Install required packages with `pip install -r requirements.txt`. You may want to create a conda (`conda create --name=wk`) or virtual environment (`python -m venv wk`) first.

2. The project works off of ".yml" config files, which hold information about your project. Create one of these per project.
- For example, cp configs/template.yml configs/W-Q.yml
- Fill in your project-specific information. You can get your webknossos token by navigating to the website and clicking your icon in the top-right corner of the screen, then clicking "Auth Token"

Run a script using: `python split_merge.py configs/W-Q.yml`

# Editing files in vim
- `vi configs/template.yml`
- Press `i` to edit and escape to stop.
- Press :wq to save and exit
- Press :q to exit without saving
- Press :q! to force exit without saving 

#  Using oscar
##  If the repo doesn't exist on your machine yet:
git clone https://github.com/drewlinsley/wk_scripts.git

##  1. load conda
module load anaconda

##  2. start a persistent screen session
- `screen`
- detatch a screen: ctrl+a (same time) then d 
- list screen sessions: screen -ls

##  3. Request our node
interact -n 8 -m 512g -t 48:00:00 -q bigmem

##  4. Load our conda env wk_merge
conda activate wk_merge

##  5. Enter your wk_scripts directory
cd wk_scripts

##  6. Run your script
python3 split_merge.py configs/template.yml

##  7. Enjoy
