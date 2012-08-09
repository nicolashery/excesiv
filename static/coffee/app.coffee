# Namespace
window.App = App = {}

App.initialize = ->
  console.log "App#initialize"

# Start the app when DOM is loaded
$ ->
  App.initialize()

