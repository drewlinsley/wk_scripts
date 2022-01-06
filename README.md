# Scripts for interacting with Webknossos.

1. Install required packages with `pip install -r requirements.txt`.

2. The project works off of ".yml" config files, which hold information about your project. Create one of these per project.
- For example, cp configs/template.yml configs/W-Q.yml
- Fill in your project-specific information. You can get your webknossos token by navigating to the website and clicking your icon in the top-right corner of the screen, then clicking "Auth Token"

Run a script using: `python split_merge.py configs/W-Q.yml`


