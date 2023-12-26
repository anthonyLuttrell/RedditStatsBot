module.exports = function(grunt) {

    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        replace: {
            js: {
                src: ['index.html'],
                overwrite: true,
                replacements: [{
                    from: /(main\.js)\?(.*)"/gi,
                    to: () => {
                        return "main.js?" + Date.now().toString() + "\"";
                    }
                }]
            },
            css: {
                src: ['index.html'],
                overwrite: true,
                replacements: [{
                    from: /(main\.css)\?(.*)"/gi,
                    to: () => {
                        return "main.css?" + Date.now().toString() + "\"";
                    }
                }]
            },
        },

        watch: {
            js: {
                files: ['js/*.js'],
                tasks: ['replace:js'],
                options: {
                    spawn: false,
                }
            },
            css: {
                files: ['css/*.css'],
                tasks: ['replace:css'],
                options: {
                    spawn: false,
                }
            }
        },
    });

    // Load the plugins you want to run
    grunt.loadNpmTasks('grunt-contrib-watch');   // https://www.npmjs.com/package/grunt-contrib-watch
    grunt.loadNpmTasks('grunt-text-replace');    // https://www.npmjs.com/package/grunt-text-replace

    // Default task(s).
    grunt.registerTask('default', ['watch']);

};