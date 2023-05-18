var merge = require('webpack-merge')
var prodEnv = require('./prod.env')
var port = 8080;
 
if (process.env.PORT != null) {
  port = process.env.PORT;
}

module.exports = merge(prodEnv, {
  NODE_ENV: '"development"',
  WEBPACK_HOST: '"localhost:'+port+'"',
  PORT: '"'+port+'"'
})
