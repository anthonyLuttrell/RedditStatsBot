### Getting started

1. IDE - Use whatever you prefer, but I highly recommend [PyCharm Community Edition](https://download.jetbrains.com/python/pycharm-community-2023.2.4.exe). First, go ahead and clone the master branch to your local PC. If you need help doing this, just ask. If you are using an IDE with Git integration, it will make your life way easier if you use that. PyCharm has a terrific Git interface.
2. The program uses [PRAW](https://praw.readthedocs.io/en/stable/index.html) to interface with Reddit, rather than directly with Reddit's API. There are a few things you will need to do first to get this working in your local environment.
   
   a. Install PRAW using `pip install praw`
   
   b. Create a new Reddit account. This will be your bot that you will use for all of your local testing.

   c. Register your bot as a script application. [Here](https://www.honchosearch.com/blog/seo/how-to-use-praw-and-crawl-reddit-for-subreddit-post-data) is a good guide on this process. The Client ID and Client Secret are the two important pieces you need. You do not need to fill out the description, about url, or redirect url. 
3. Now that you have your bot's username, password, Client ID, and Client Secret, you need to create a `praw.ini` file to store this sensitive data in. This file should always stay on your local PC, it should never be checked into any version control software (like Git), and you should never share it with anyone else. It is already in the `.gitignore` file, which prevents Git from including it in any push/pulls that you do. For now, everything is in one directory, so just create a new file right along side everything else and name it `praw.ini`. The contents of this file are simple: 

   ```
   [AnyCommonName]
   client_id: YourClientID
   client_secret: YourClientSecret 
   username: YourBotUsername
   password: YourBotPassword
   ```
   
4. Create a new subreddit to be used for a sandbox testing environment. You will need to add your bot as a mod. Make some test posts and test comments.
5. There are three lines in `main.py` that you will have to change to get the bot to run on your newly created subreddit.

   a. `BOT_NAME = "CookingStatsBot"`: replace `CookingStatsBot` with whatever you entered for `AnyCommonName` in your `praw.ini` file. 
   
   b. `REDDIT = praw.Reddit(BOT_NAME, user_agent="r/Cooking Stats Bot by u/96dpi")`: replace the `user_agent` text with a very brief description on your bot and your Reddit username. 
   
   c. `SUB = "Cooking"`: replace `Cooking` with your newly created subreddit. 

Now you should be able to run the program from either your IDE, or through a command prompt. There should be some basic print statements giving you info, and once the main loop finishes, you can check the `stats.json` file to see the data it collected. You may want to change the `SLEEP_TIME_SECONDS` constant to just a few seconds. Just inline comment out everything to the right of the `=` and stick an integer in there before the comment. 

BTW, you can actually run this in "read-only" mode on any subreddit. You will just have to comment out the lines where it actually tries to edit user flair and the reddit's wiki page.
