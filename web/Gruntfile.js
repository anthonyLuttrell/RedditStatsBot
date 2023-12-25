module.exports = function(grunt) {

    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        uglify: {
            options: {
                banner: '/*! <%= pkg.name %>.js last minified on <%= grunt.template.today("yyyy-mm-dd") %> */\n'
            },
            build: {
                src: 'js/<%= pkg.name %>.js',
                dest: 'build/js/<%= pkg.name %>.min.js'
            }
        },

        cssmin: {
            options: {
                mergeIntoShorthands: false,
                roundingPrecision: -1
            },
            target: {
                files: {
                    'build/css/main.css': ['css/main.css', 'css/normalize.css']
                },
            }
        },

        htmlmin: {
            dist: {
                options: {
                    removeComments: true,
                    collapseWhitespace: true
                },
                files: {
                    'build/index.html': 'build/index.html',
                }
            }
        },

        replace: {
            js: {
                src: ['build/index.html'],
                dest: 'build/',
                replacements: [{
                    from: /(main\.js)\?(.*)"/gi,
                    to: () => {
                        return "main.js?" + Date.now().toString() + "\"";
                    }
                }]
            },
            css: {
                src: ['build/index.html'],
                dest: 'build/',
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
                tasks: ['replace:js', 'uglify', 'htmlmin'],
                options: {
                    spawn: false,
                }
            },
            css: {
                files: ['css/*.css'],
                tasks: ['replace:css', 'cssmin', 'htmlmin'],
                options: {
                    spawn: false,
                }
            }
        },
    });

    // Load the plugins you want to run
    grunt.loadNpmTasks('grunt-contrib-watch');   // https://www.npmjs.com/package/grunt-contrib-watch
    grunt.loadNpmTasks('grunt-contrib-uglify');  // https://www.npmjs.com/package/grunt-contrib-uglify
    grunt.loadNpmTasks('grunt-contrib-cssmin');  // https://www.npmjs.com/package/grunt-contrib-cssmin
    grunt.loadNpmTasks('grunt-contrib-htmlmin'); // https://www.npmjs.com/package/grunt-contrib-htmlmin
    grunt.loadNpmTasks('grunt-text-replace');    // https://www.npmjs.com/package/grunt-text-replace

    // Default task(s).
    grunt.registerTask('default', ['watch']);

};