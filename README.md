### Getting started

1. IDE - Use whatever you prefer, but I highly recommend [PyCharm Community Edition](https://download.jetbrains.com/python/pycharm-community-2023.2.4.exe). First, [clone](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) the master branch to your local PC. If you are using an IDE with Git integration, it will make your life way easier if you use that. PyCharm has a terrific Git interface. All commits should be pushed to the `dev` branch, or you can create a new branch. 

2. The program uses [PRAW](https://praw.readthedocs.io/en/stable/index.html) to interface with Reddit, rather than directly with Reddit's API. There are a few things you will need to do first to get this working in your local environment.
   
   a. Install PRAW using `pip install praw`
   
   b. Create a new Reddit account. This will be your bot that you will use for all of your local testing.

   c. Register your bot as a script application. [Here](https://www.honchosearch.com/blog/seo/how-to-use-praw-and-crawl-reddit-for-subreddit-post-data) is a good guide on this process, but you must select the script option! The Client ID and Client Secret are the two important pieces you need. You do not need to fill out the description, about url, or redirect url. 

3. Now that you have your bot's username, password, Client ID, and Client Secret, you need to create a `praw.ini` file to store this sensitive data in. This file should always stay on your local PC, it should never be checked into any version control software (like Git), and you should never share it with anyone else. It is already in the `.gitignore` file, which prevents Git from including it in any push/pulls that you do. For now, everything is in one directory, so just create a new file right along side everything else and name it `praw.ini`. The contents of this file are simple: 

   ```
   [YourBotUsername]
   client_id: YourClientID
   client_secret: YourClientSecret 
   username: YourBotUsername
   password: YourBotPassword
   ```
   

4. Create a new subreddit to be used for a sandbox testing environment. You will need to add your bot as a mod. Make some test posts and test comments.

5. In `scanner_pool.py`, there is an object called `scanner_class_builder`. Change the string after `bot_name=` to be your newly created bot account name.

6. Also in `scanner_pool.py`, add your newly created testing subreddit to the `subreddit_list`. 

When you run the program, it will scan each sub in this list, so feel free to add or remove whatever you'd like. Only subs where your bot has user flair and wiki permissions will be able to actually change anything. Debug output is saved to `json/debug.log`.

---

### Web

1. Similar to the `praw.ini` file, you will need an `ftp.ini` file that stores your FTP log-in credentials.
   * If you will be working on the web portion of this project, I can create a new FTP account for you upon request, and that is what you will use to fill out your `ftp.ini` file.
   * If you will not be working on the web portion, you will need to comment out the code in `ftp.py` for now (keep the `send_file` function, just replace its body with `pass`), until we figure out a better solution. 
   * The `ftp.ini` file should be stored in the root directory of the project and its contents should be: 
     ```
     [ftp]
     server_address: redditstatsbot.com
     username: YourFTPUsername
     password: YourFTPPassword
     ```
   * This file should always stay on your local PC, it should never be checked into any version control software (like Git), and you should never share it with anyone else. It is already in the `.gitignore` file, which prevents Git from including it in any push/pulls that you do.


