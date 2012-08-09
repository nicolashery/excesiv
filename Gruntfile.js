module.exports = function(grunt) {

  // Project configuration
  grunt.initConfig({
    // Project metadata
    meta: {
      // Put banner with project name on top of concatenated files
      banner: '/*! Excesiv | <%= grunt.template.today("yyyy-mm-dd") %> */'
    },

    // Compile coffee files to js
    coffee: {
      app: {
        src: ['static/coffee/*.coffee'],
        dest: 'static/js',
        options: {
          bare: true
        }
      }
    },

    // Compile sass files to css using Compass
    compass: {
      style: {
        src: 'static/sass',
        dest: 'static/css',
        outputstyle: 'expanded',
        linecomments: false
      }
    },

    // Watch all source files and compile when changed, use for development
    watch: {
      files: ['static/coffee/*.coffee', 'static/sass/*.scss'],
      tasks: 'coffee compass'
    },

    // Concatenate files
    concat: {
      vendor: {
        src: ['<banner:meta.banner>',
              'static/js/vendor/jquery.js',
              'static/js/vendor/jquery.ui.widget.js',
              'static/js/vendor/jquery.iframe-transport.js',
              'static/js/vendor/jquery.fileupload.js'],
        dest: 'static/build/vendor.js'
      },
      app: {
        src: ['<banner:meta.banner>',
              'static/js/app.js'],
        dest: 'static/build/app.js'
      },
      style: {
        src: ['<banner:meta.banner>',
              'static/css/style.css'],
        dest: 'static/build/style.css'
      }
    },

    // Minify js files
    min: {
      vendor: {
        src: ['<config:concat.vendor.dest>'],
        dest: 'static/build/vendor.min.js'
      },
      app: {
        src: ['<config:concat.app.dest>'],
        dest: 'static/build/app.min.js'
      },
    },

    // Minify css files
    cssmin: {
      style: {
        src: ['<config:concat.style.dest>'],
        dest: 'static/build/style.min.css'
      }
    }

  });

  // Load tasks from NPM packages
  grunt.loadNpmTasks('grunt-coffee'); // https://github.com/avalade/grunt-coffee 
  grunt.loadNpmTasks('grunt-compass'); // http://github.com/kahlil/grunt-compass
  grunt.loadNpmTasks('grunt-css'); // https://github.com/jzaefferer/grunt-css

  // Default task: build deployment
  grunt.registerTask('default', 'coffee compass concat min cssmin');

};
