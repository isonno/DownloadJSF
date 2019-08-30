downloadJSF
===========

This script downloads all of your fiddles from the [JSFiddle.net](https://jsfiddle.net) web site. 
This gives you a convenient way to backup your work or make them available for local development.
The files are each saved as a single HTML file containing the script, HTML, and CSS.

### Setup

The script is written in [Python3](https://www.python.org). It also uses the [Requests](https://2.python-requests.org/en/master/)
library, which is installed with

    sudo python3 -m pip install requests

(the `sudo` prefix may or may not be necessary depending on your system configuration). The script's `#!` directive assumes Python3 is in `/usr/local/bin/python3`, you may need to revise that for your configuration.

### Usage

Simply running the scripts prompts for your JSFiddle.net login credentials, and downloads all of the fiddles on your account to a folder named `fiddles/` in the current directory.

The script has the following command line arguments:

* `-u` _email_ 
    * specifies the email address used to log into JSFiddle.net. Prompts if not supplied.
* `-p` _password_
    * Password for your JSFiddle.net account. Prompts if not supplied.
* `-d` _destination folder_
    * Folder fiddles are written to. Default is `fiddles` in the current directory.
* `-n`
    * If specified, no attempt is made to fix the script URL in the file (e.g., for JQuery).
* `-l`
    * Just list the fiddles, do not download them.

