'use strict';

module.exports = function (grunt) {

    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        src: './application/static_src',
        images: './application/static/images/',
        dest: './application/static/<%=pkg.version%>',
        mapping: grunt.file.readJSON('./application/static_src/mapping.json'),
        files: grunt.file.readJSON('./application/static_src/files.json'),
        // Clean
        clean: {
            images: "<%=images%>",
            js: "<%=dest%>/js",
            css: ["<%=dest%>/font-awesome", "<%=dest%>/css"],
            mmgmt: ["<%=dest%>/mmgmt"]
        },

        // Copy resource files
        copy: {
            images: {
                expand: true,
                cwd: '<%=src%>/images/',
                src: '**',
                dest: '<%=images%>'
            },
            mmgmt: {
                expand: true,
                cwd: '<%=src%>/mmgmt/',
                src: '**',
                dest: '<%=dest%>/mmgmt'
            },
            "font-awesome": {
                expand: true,
                cwd: '<%=src%>/font-awesome',
                src: ['**/*.css', '**/*.eot', '**/*.svg', '**/*.ttf', '**/*/woff', '**/*.woff2', '**/*.otf'],
                dest: '<%=dest%>/font-awesome/'
            },
            footable: {
                expand: true,
                cwd: '<%=src%>/css/plugins/footable',
                src: ['**/*.css', '**/*.eot', '**/*.svg', '**/*.ttf', '**/*.woff'],
                dest: '<%=dest%>/css/plugins/footable'
            },
            jsGrid:{
                expand: true,
                cwd: '<%=src%>/css',
                src: ['jsgrid.css', 'jsgrid-theme.css'],
                dest: '<%=dest%>/css'
            },
            chosen:{
                expand: true,
                cwd: '<%=src%>/css/plugins/chosen',
                src: ['*.css', '*.png'],
                dest: '<%=dest%>/css/plugins/chosen'
            },
            zeroclipboard: {
                expand: true,
                cwd: '<%=src%>/vender/plugins/zeroclipboard/',
                src: 'ZeroClipboard.swf',
                dest: '<%=images%>'
            }
        },
        // Prepare css files
        sass: {
            //watch: {
            //    options: {
            //        sourcemap: true,
            //        trace: false,
            //        style: "nested",
            //        lineNumbers: true,
            //        watch: true,
            //        loadPath: ['<%=src%>/SCSS', '<%=src%>/SCSS/plugins'],
            //    },
            //    files: {
            //        '<%=dest%>/css/style.css': '<%=src%>/SCSS/style.scss'
            //    }
            //},
            dev: {
                options: {
                    sourcemap: true,
                    trace: false,
                    style: "nested",
                    lineNumbers: true,
                    loadPath: ['<%=src%>/SCSS', '<%=src%>/SCSS/plugins']
                },
                files: {
                    '<%=dest%>/css/style.css': '<%=src%>/SCSS/style.scss',
                    '<%=dest%>/css/funnel-chart.css': '<%=src%>/scss_vender/funnel-chart.scss'
                }
            },
            deploy: {
                options: {
                    sourcemap: false,
                    trace: false,
                    style: "compressed",
                    loadPath: ['<%=src%>/SCSS', '<%=src%>/SCSS/plugins']
                },
                files: {
                    '<%=dest%>/css/style.css': '<%=src%>/SCSS/style.scss',
                    '<%=dest%>/css/funnel-chart.css': '<%=src%>/scss_vender/funnel-chart.scss'
                }
            }
        },

        // Shampoo
        shampoo: {
            deploy: {
                options: {
                    map: '<%=mapping%>',
                    watch: false,
                    sourceMaps: false
                },
                files: '<%=files%>'
            },
            watch: {
                options: {
                    map: '<%=mapping%>',
                    watch: true,
                    sourceMaps: true
                },
                files: '<%=files%>'
            },
            dev: {
                options: {
                    map: '<%=mapping%>',
                    watch: false,
                    sourceMaps: true
                },
                files: '<%=files%>'
            }
        },

        uglify: {
            deploy: {
                files: [{
                    expand: true,
                    cwd: '<%=dest%>/js',//js目录下
                    src: '**/*.js',//所有js文件
                    dest: '<%=dest%>/js'//输出到此目录下
                }]
            }
        }
    });
    grunt.loadTasks("shampoo/tasks");

    grunt.loadNpmTasks('grunt-contrib-sass');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks("grunt-contrib-jshint");
    grunt.loadNpmTasks("grunt-contrib-clean");
    grunt.loadNpmTasks("grunt-contrib-nodeunit");
    grunt.loadNpmTasks("grunt-contrib-connect");
    grunt.loadNpmTasks('grunt-contrib-copy');

    grunt.registerTask("dev", ['clean', 'copy', 'shampoo:dev', 'sass:dev']);
    grunt.registerTask("watch", ['clean', 'copy', 'shampoo:watch', 'sass:dev']);
    grunt.registerTask("deploy", ['clean', 'copy', 'shampoo:deploy', 'sass:deploy', "uglify:deploy"]);

    grunt.registerTask("default", "deploy");
};
