#!/usr/local/bin/python3
#
# Download all your fiddles from JSFiddle.net.
#
# This uses the requests library, which is not part of the standard Python3
# release. Use:
#    sudo python3 -m pip install requests
# to get a copy.
#
# See https://stackoverflow.com/questions/9851878/is-there-a-download-function-in-jsfiddle
# Also https://pybit.es/requests-session.html for some tips on requests
#
# J. Peterson, August 2019

import requests, os, re, sys, argparse, getpass
from html.parser import HTMLParser

# These URLs work as of August 2019
loginURL = "https://jsfiddle.net/user/login/"
userListURL = "https://jsfiddle.net/user/fiddles/all/"
# First param is username, second is the fiddle ID
fiddleURL = "https://fiddle.jshell.net/%s/%s/show/light/"

# Clunky code concocting a name/value pair from the HTML attributes
def getEntryFromAttr(attr):
    items = [a for a in attr if a[0] in ['name', 'value']]
    value = ""
    name = ""
    if (len(items) ==2):
       name = [a for a in items if a[0] =='name'][0][1]
       value = [a for a in items if a[0] == 'value'][0][1]
    else:
        if items[0][0] == 'name':
            name = items[0][1]
    return name, value

# Parse the login page to get the session IDs needed.
class ParseLogin(HTMLParser):
    def __init__(self):
        self.attrList = []
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if (tag != "input"):
            return
        self.attrList.append(attrs)

    def getInputKeys(self):
        resultDict = {}
        for i in self.attrList:
            entry = getEntryFromAttr(i)
            if (entry[0] != ''):
                resultDict[entry[0]] = entry[1]
        return resultDict

# Parse the fiddles page to get the IDs and titles
class ParseFiddles(HTMLParser):
    def __init__(self):
        self.fiddleList = {}
        self.parsingAnchor = False
        self.userName = None
        self.fiddleID = ""
        self.nextPages = set()
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if (tag != 'a'):
            return

        if (len(attrs) == 1 and attrs[0][0] == 'href' and re.match("[/]\w+[/]\w+[/](\d+[/])*$", attrs[0][1])):
            m = re.match("[/](\w+)[/](\w+)[/]", attrs[0][1])
            self.fiddleID = m.group(2)
            # Skip these "ID"s, they're structural
            if not (self.fiddleID in ['groups', 'logout']):
                self.userName = m.group(1)
                self.parsingAnchor = True
        elif (len(attrs) == 1 and attrs[0][0] == 'href'):
            m = re.match("[/]user[/]fiddles[/]all[/](\d+)/", attrs[0][1])
            if m:
                self.nextPages.add(m.group(1))

    def handle_data(self, data):
        if (self.parsingAnchor):
            self.fiddleList[self.fiddleID] = data
            self.parsingAnchor = False

    def handle_endtag(self,tag):
        if (tag == 'a'):
            self.parsingAnchor = False

# Hard coded copy of the headers expected by the JSFiddle web site
# (Captured w/Chrome debugger)
JSFheaders = {'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
'accept-encoding': "gzip, deflate, br",
'accept-language': "en-US,en;q=0.9",
'cache-control': "max-age=0",
'content-type': 'application/x-www-form-urlencoded',
'origin': 'https://jsfiddle.net',
'referer': 'https://jsfiddle.net/user/login/',
'sec-fetch-mode': 'navigate',
'sec-fetch-site': 'same-origin',
'sec-fetch-user': '?1',
'upgrade-insecure-requests': '1',
'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 downloadJSF/0.8'}

# If a fiddle refers to a script library, restore the "https:" that gets stripped out.
def fixupScriptURL(fidSource):
    m = re.search('<script.*?src="([/][/]\w+[\w/.-]*)"\s*>\s*<[/]script>', fidSource, re.DOTALL)
    return fidSource.replace(m.group(1), "https:" + m.group(1), 1) if m else fidSource

def main():
    destFolder = "fiddles"

    # Extract arguments from the command line
    getargs = argparse.ArgumentParser(description="Download fiddles from JSFiddle.net")
    getargs.add_argument('--user', '-u', nargs=1, metavar='email', default=None,
                        help="User email address to log in to JSFiddle.net")
    getargs.add_argument('--password', '-p', nargs=1, metavar='password', default=None,
                        help="Password to log into JSFiddle.net")
    getargs.add_argument('--dest', '-d', nargs=1, metavar='destination', default=[destFolder],
                        help="Destination folder to save fiddles to")
    getargs.add_argument('--nofixurl', '-n', action='store_true', default=False,
                        help="Skip fixing the script URL when fiddles are downloaded")
    getargs.add_argument('--list', '-l', action="store_true", default=False,
                        help="Only list fiddles, do not download them")
    args = getargs.parse_args( sys.argv[1:] )

    if (not args.user):
        args.user = [input("JSFiddle user email address:")]

    if (not args.password):
        args.password = [getpass.getpass()]

    if (args.dest):
        destFolder = args.dest[0]

    if (not os.path.exists(destFolder)):
        print("Creating destination folder...")
        os.mkdir(destFolder)

    # Web site processing
    print("Logging in...")
    loginSession = requests.get(loginURL)
    parser = ParseLogin()
    parser.feed(loginSession.text)
    loginDict = parser.getInputKeys()
    loginDict['email'] = args.user[0]
    loginDict['password'] = args.password[0]
    post = requests.post(loginURL, data=loginDict, headers=JSFheaders, cookies=loginSession.cookies)
    if (re.search(".*enter a correct login and password", post.text)):
        print("Login failed.")
        sys.exit(-1)

    print("Get Fiddle list...")
    fiddleListPage = requests.get(userListURL, headers=JSFheaders, cookies=post.cookies)
    fiddleListParser = ParseFiddles()
    fiddleListParser.feed(fiddleListPage.text)
    extraPages = sorted(list(fiddleListParser.nextPages))
    for page in extraPages:
        nextFiddlePage = requests.get(userListURL + page, headers=JSFheaders, cookies=post.cookies)
        fiddleListParser.feed(nextFiddlePage.text)

    keepcharacters = (' ','.','_')

    # Download (or list) the fiddles found.
    if (args.list):
        print("Fiddles for %s:", fiddleListParser.userName)
        for k in fiddleListParser.fiddleList.keys():
            print(" [%s] %s..." % (k, fiddleListParser.fiddleList[k]))
    else:
        for k in fiddleListParser.fiddleList.keys():
            fiddleName = fiddleListParser.fiddleList[k]
            print("Downloading fiddle [%s] %s..." % (k, fiddleName))
            fid = requests.get(fiddleURL % (fiddleListParser.userName, k), headers=JSFheaders, cookies=post.cookies)
            # Clean possibly problematic gunk out of the filename
            fileName = "".join(c for c in fiddleName if c.isalnum() or c in keepcharacters).rstrip()
            fiddleText = fid.text if args.nofixurl else fixupScriptURL(fid.text)
            open("%s%s%s.html" % (destFolder, os.path.sep, fileName), 'w').write(fiddleText)

        print("...Done.")

main()
