// vue.config.js
const { defineConfig } = require('@vue/cli-service');
const path = require('path');
const webpack = require('webpack');
const MomentLocalesPlugin = require('moment-locales-webpack-plugin');
const port = process.env.PORT ? parseInt(process.env.PORT) : 9122;

module.exports = defineConfig({
    runtimeCompiler: true,
    outputDir: path.resolve(__dirname, '../../static/mooringlicensing_vue'),
    publicPath: '/static/mooringlicensing_vue/',
    filenameHashing: false,
    chainWebpack: (config) => {
        config.resolve.alias.set(
            '@',
            path.resolve(__dirname, 'src')
        );
        config.resolve.alias.set(
            '@vue-utils',
            path.resolve(__dirname, 'src/utils/vue')
        );
        config.resolve.alias.set(
            '@common-utils',
            path.resolve(__dirname, 'src/components/common/')
        );
        config.resolve.alias.set(
            '@static-root',
            path.resolve(__dirname, '../../../staticfiles_ml/')
        );
        config.resolve.alias.set(
            'datetimepicker',
            path.resolve(__dirname, 'eonasdan-bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js')
        )
    },
    configureWebpack: {
        devtool: 'source-map',
        resolve: {
            fallback: {
                buffer: require.resolve('buffer/'),
            },
        },
        plugins: [
            new webpack.ProvidePlugin({
                $: 'jquery',
                jQuery: 'jquery',
                moment: 'moment',
                swal: 'sweetalert2',
                _: 'lodash',
                "select2": "../node_modules/select2/dist/js/select2.full.min.js",
                datetimepicker:"../node_modules/eonasdan-bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js"
            }),
            new MomentLocalesPlugin(),
            new webpack.ProvidePlugin({
                Buffer: ['buffer', 'Buffer'],
            }),
        ],
        devServer: {
            host: '0.0.0.0',
            allowedHosts: 'all',
            devMiddleware: {
                //index: true,
                writeToDisk: true,
            },
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers':
                    'Origin, X-Requested-With, Content-Type, Accept',
            },
            client: {
                webSocketURL: 'ws://0.0.0.0:' + port + '/ws',
            },
        },
        module: {
            rules: [
                {
                    test: /\.(png|jpe?g|gif|webp|avif)(\?.*)?$/,
                    type: 'asset/resource',
                    generator: {
                        filename: 'img/[name][ext]',
                    },
                },
                {
                    test: /\.(woff2?|eot|ttf|otf)(\?.*)?$/i,
                    type: 'asset/resource',
                    generator: {
                        filename: 'fonts/[name][ext]',
                    },
                },
            ],
        },
        performance: {
            hints: false,
        },
    },
});