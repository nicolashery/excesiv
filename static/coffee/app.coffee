# Namespace
window.App = App = {}

# Properties
App.message = 'Hello World!'
App.response = ''
App.waiting = false # Indicates we are waiting for a response

App.initialize = ->
  # Cache elements
  @$message = $("input[name='message']")
  @$output = $('.js-download-result')
  # Bind events
  $('.js-send').on('click', => @onSend())
  # File upload widget
  @initFileUpload()

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
    url: '/api/write/demo'
    data:
      message: @message
    beforeSend: =>
      @print "<p>Waiting for response...</p>"
      @waiting = true
    success: (data) =>
      @response = data.message
      output = "<p><a href='#{data.file_url}'>Download file</a></p>"
      @print output
      @waiting = false

# Print an HTML message in output area
App.print = (html) ->
  @$output.html html
  @

App.initFileUpload = ->
  $('#fileupload').fileupload(

    url: '/api/read/demo'

    dataType: 'json'

    dropZone: $('#filedrop')

    add: (e, data) ->
      if data.files[0].name.match(/\.xlsx$/)
        $('.js-upload-result').html "<p>Waiting for response...</p>"
        data.submit()
      else
        $('.js-upload-result').html "<p>Only accepts .xlsx files</p>"

    done: (e, data) ->
      $('.js-upload-result').html "<p>Response: #{data.result.response}</p>"

  )
  # Disable default browser action for file drops
  $(document).bind 'drop dragover', (e) ->
    e.preventDefault()
  @
  # Bind events to change drop zone style when file dragged over
  $filedrop = $('#filedrop')
  $filedrop.on 'dragover', (e) ->
    $filedrop.addClass 'hover'
  $filedrop.on 'dragleave', (e) ->
    $filedrop.removeClass 'hover'
  $filedrop.on 'drop', (e) ->
    $filedrop.removeClass 'hover'

# Start the app when DOM is loaded
$ ->
  App.initialize()
