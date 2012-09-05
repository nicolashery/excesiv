(($) ->

  # APP
  # ==========================================================================

  # Application object
  App = {}
  # Two components to the app
  Writer = App.Writer = {}
  Reader = App.Reader = {}

  # Messages
  messages = App.messages =
    error: '<span class="error">Oops! An error occured. Please try <a href="/">refreshing</a> the page.</span>'
    download: (fileUrl) ->
      "<a href='#{fileUrl}'>Download Excel file</a>"

  # Start the application
  App.initialize = ->
    @Writer.initialize()
    @Reader.initialize()

  # WRITER
  # ==========================================================================

  # Indicates if we are waiting for server to write to Excel workbook
  Writer.busy = false

  # Default parameter values
  Writer.nRowsDefault = 10
  Writer.randMaxDefault = 3

  Writer.initialize = ->
    # Data model
    @model =
      n_rows: @nRowsDefault
      rand_max: @randMaxDefault
    # Cache elements
    @$nRows = $("input[name='n_rows']")
    @$randMax = $("input[name='rand_max']")
    @$submit = $('#js-writer-submit')
    @$message = $('#js-writer-message')
    # Set default values
    @$nRows.val(@nRowsDefault)
    @$randMax.val(@randMaxDefault)
    # Bind events
    @$submit.click $.proxy(@onSubmit, @)

  # On form submit, if inputs valid, send request to server
  Writer.onSubmit = (e) ->
    e?.preventDefault()
    if @validateForm()
        # Prepare data
        data = JSON.stringify(@model)
        # Send AJAX request
        $.ajax
          url: '/api/write/demo'
          type: 'POST'
          contentType: 'application/json'
          data: data
          beforeSend: =>
            @toggleBusy() # Freeze form
            @$message.html("") # Empty message
          success: (data) =>
            # Print download link to file
            @$message.html messages.download(data.file_url)
          error: =>
            @$message.html messages.error
          complete: =>
            @toggleBusy() # Unlock form

  # Toggle between busy and idle states
  Writer.toggleBusy = ->
    if @busy
      # Unlock inputs and button
      @$nRows.prop('disabled', false)
      @$randMax.prop('disabled', false)
      @$submit.prop('disabled', false)
      @$submit.text('Generate')    
      @busy = false
    else
      # Disable inputs and button
      @$nRows.prop('disabled', true)
      @$randMax.prop('disabled', true)
      @$submit.prop('disabled', true)
      @$submit.text('Loading...')
      @busy = true
    @

  # Validate form, reset fields if needed, and return true or false
  Writer.validateForm = ->
    isValid = true
    # For each validation function, if it returns false, form is invalid
    unless @validateNRows()
      isValid = false
    unless @validateRandMax()
      isValid = false
    return isValid

  # Validate n_rows field, reset to default value if invalid, 
  # return true or false
  Writer.validateNRows = ->
    min = 1
    max = 100
    val = @$nRows.val()
    val = parseInt(val*1) # Try to convert string to integer
    if isNaN(val) or (!isNaN(val) and (val <= min or val >= max))
      @$nRows.val(@nRowsDefault) # Reset to default value
      @model.n_rows = @nRowsDefault
      return false
    else
      @$nRows.val(val) # Reset to converted integer (ex: if was float)
      @model.n_rows = val # Update model
      return true

  # Validate rand_max field, reset to default value if invalid, 
  # return true or false
  Writer.validateRandMax = ->
    min = 1
    max = 100
    val = @$randMax.val()
    val = parseFloat(val*1) # Try to convert string to float
    if isNaN(val) or (!isNaN(val) and (val <= min or val >= max))
      @$randMax.val(@randMaxDefault) # Reset to default value
      @model.rand_max = @randMaxDefault
      return false
    else
      @model.rand_max = val # Update model
      return true

  # READER
  # ==========================================================================

  # Indicates if we are waiting for server to read Excel workbook
  Reader.busy = false

  Reader.initialize = ->

  # Toggle between busy and idle states
  Reader.toggleBusy = ->
    if @busy
      @busy = false
    else
      @busy = true
    @

  # START
  # ==========================================================================

  # Start the app when DOM is loaded
  $ ->
    App.initialize()
    window.App = App

)(jQuery)
