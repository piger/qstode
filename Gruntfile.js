module.exports = function (grunt) {
    var env = {
        js_root: 'qstode/static/js',
        css_root: 'qstode/static/css'
    };

    // Project configuration
    grunt.initConfig({
        env: env,
        pkg: grunt.file.readJSON('package.json'),

        less: {
            development: {
                options: {
                    paths: ["qstode/static/css"],
                    cleancss: true
                },
                files: {
                    "<%= env.css_root %>/qstode.min.css": "<%= env.css_root %>/qstode.less",
                    "<%= env.css_root %>/popup.min.css": "<%= env.css_root %>/popup.less"
                }
            }
        },

        uglify: {
            options: {
                banner: '/*! <%= pkg.name %> <%= pkg.version %>, generated on: <%= grunt.template.today("yyyy-mm-dd") %> */\n'
            },
            build: {
                files: {
                    '<%= env.js_root %>/qstode.min.js': [
                        '<%= env.js_root %>/qstode.js'
                    ]
                }
            }
        },

        jshint: {
            files: ['Gruntfile.js', '<%= env.js_root %>/qstode.js'],
            options: {
                globals: {
                    jQuery: true,
                    console: true,
                    module: true
                }
            }
        },

        watch: {
            hint: {
                files: ['<%= jshint.files %>'],
                tasks: ['jshint']
            },
            /*
             js: {
             files: ['<% env.js_root %>/*.js'],
             tasks: ['uglify']
             },
             */
            css: {
                files: ['<%= env.css_root %>/*.less'],
                tasks: ['less'],
                options: {
                    livereload: true
                }
            }
        }
    });

    // load tasks
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-less');
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-watch');

    // register tasks
    grunt.registerTask('default', ['less', 'uglify']);
    // grunt.registerTask('watchless', ['watch']);
};
