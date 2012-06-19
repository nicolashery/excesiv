# Namespace
window.App = App = {}

# Properties
App.message = 'Hello World!'
App.response = ''
App.waiting = false # Indicates we are waiting for a response

App.initialize = ->
  # Cache elements
  @$message = $("input[name='message']")
  @$output = $('.js-output')
  # Bind events
  $('.js-send').on('click', => @onSend())

App.onSend = ->
  # Don't do anything if we are already waiting for response
  if @waiting
    return false
  # Grab message from input
  @message = @$message.val()
  # Don't allow empty message
  if not @message.length
    return @print "<p>Message can't be empty.</p>"
  # Trim if longer than 140 chars
  if @message.length > 140
    @message = @message[0..139]
  $.ajax
    url: '/api/demo/'
    data:
      message: @message
    beforeSend: =>
      @print "<p>Waiting for response...</p>"
      @waiting = true
    success: (data) =>
      @response = data.message
      output = """
               <p><strong>Message</strong>: #{@message}</p>
               <p><strong>Response</strong>: #{@response}</p>
               """
      @print output
      @waiting = false

# Print an HTML message in output area
App.print = (html) ->
  @$output.html html
  @

# Start the app when DOM is loaded
$ ->
  App.initialize()
