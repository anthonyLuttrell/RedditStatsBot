## How to configure Grunt for your local environment

### Prerequisites:

* All query strings in the `index.html` file that you want to overwrite must already have an existing query string. For example:

  `<script src="js/main.js"></script>` will not work. It must be:

  `<script src="js/main.js?anyString"></script>`

1. Install [node.js](https://nodejs.org/en/download)
2. Install the Grunt CLI `npm install -g grunt-cli`
3. Install these Grunt plugins:
   - `npm install grunt-contrib-watch --save-dev`
   - `npm install grunt-text-replace --save-dev`

Everything is now installed and ready to use, but you will still have to manually launch the Grunt default task. 

### How to launch the Grunt task:

1. Open a terminal within the same directory that the `Gruntfile.js` is located (`your_project_root\web`) 
   - **Note:** you can do this within most editors/IDEs.
2. Run the command `grunt`. It will stay active until you close the terminal or use Ctrl+C to cancel it. 

The terminal should now look like this:

![](https://i.imgur.com/7iyeyXz.png)

Note: Depending on your IDE/editor, there may be a way to make this launch automatically as well. I am still researching this. 

### How it works:

Whenever you make a change to any JavaScript or CSS file, it will automatically update the query string after the file name. The watch task is always running, and it contains two sub-tasks. The process goes like this:

1. Task `js`: will run whenever any JavaScript file is modified. It currently only supports `main.js`. It does the following: 
   - Overwrites the query string for `main.js` in the `index.html` file to the current epoch time.
2. Task `css` will run whenever any CSS files are modified. It does the following:
   - Overwrites the query string for `main.css` in the `index.html` file to the current epoch time.

### Warnings:

This is a destructive process, it is modifying the original file and not creating a backup. Any changes to `Gruntfile.js` should be done with care.