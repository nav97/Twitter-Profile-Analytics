# Tweet-Analyzer

### Installation

To install all the required libraries:
```sh
pip install -r requirements.txt
```
Requires Python version 2.7+

### Usage 

After installing all the required libraries the user must place their Twitter API keys in the `auth.py` file. These keys can be obtained from  https://apps.twitter.com/

```
usage: -n <screen_name> [options]

Twitter Profile Analyzer (https://github.com/nav97/Tweet-Analyzer)

optional arguments:
  -h, --help            show this help message and exit
  -n screen_name, --name screen_name
                        The specified twitter user screen name
  -l N, --limit N       Specify the number of tweets to retrieve going back
                        from the latest tweet (default to 1000)
  --utc-offset UTC_OFFSET
                        Apply timezone offset (in seconds)
  --no-timezone         Remove timezone auto-adjustment (default to UTC)
```

### Example
![alt tag](https://raw.githubusercontent.com/nav97/Tweet-Analyzer/master/Screenshots/Capture1.PNG)
![alt tag](https://raw.githubusercontent.com/nav97/Tweet-Analyzer/master/Screenshots/Capture2.PNG)
![alt tag](https://raw.githubusercontent.com/nav97/Tweet-Analyzer/master/Screenshots/Capture3.PNG)
