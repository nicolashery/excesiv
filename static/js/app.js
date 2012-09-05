
(function($) {
  var App, Reader, Writer, messages;
  App = {};
  Writer = App.Writer = {};
  Reader = App.Reader = {};
  messages = App.messages = {
    error: '<span class="error">Oops! An error occured. Please try <a href="/">refreshing</a> the page.</span>',
    downloadLink: function(fileUrl) {
      return "<a href='" + fileUrl + "'>Download Excel file</a>";
    },
    wrongFileType: '<span class="error">Sorry! We only accept .xslx files.</span>',
    readerResult: function(result) {
      result = JSON.stringify(result, void 0, 2);
      return "<pre>" + result + "</pre>";
    }
  };
  App.initialize = function() {
    this.Writer.initialize();
    return this.Reader.initialize();
  };
  Writer.busy = false;
  Writer.nRowsDefault = 10;
  Writer.randMaxDefault = 3;
  Writer.initialize = function() {
    this.model = {
      n_rows: this.nRowsDefault,
      rand_max: this.randMaxDefault
    };
    this.$nRows = $("input[name='n_rows']");
    this.$randMax = $("input[name='rand_max']");
    this.$submit = $('#js-writer-submit');
    this.$message = $('#js-writer-message');
    this.$nRows.val(this.nRowsDefault);
    this.$randMax.val(this.randMaxDefault);
    return this.$submit.click($.proxy(this.onSubmit, this));
  };
  Writer.onSubmit = function(e) {
    var data,
      _this = this;
    if (e != null) {
      e.preventDefault();
    }
    if (this.validateForm()) {
      data = JSON.stringify(this.model);
      return $.ajax({
        url: '/api/write/demo',
        type: 'POST',
        contentType: 'application/json',
        data: data,
        beforeSend: function() {
          _this.toggleBusy();
          return _this.$message.html("");
        },
        success: function(data) {
          return _this.$message.html(messages.downloadLink(data.file_url));
        },
        error: function() {
          return _this.$message.html(messages.error);
        },
        complete: function() {
          return _this.toggleBusy();
        }
      });
    }
  };
  Writer.toggleBusy = function() {
    if (this.busy) {
      this.$nRows.prop('disabled', false);
      this.$randMax.prop('disabled', false);
      this.$submit.prop('disabled', false);
      this.$submit.text('Generate');
      this.busy = false;
    } else {
      this.$nRows.prop('disabled', true);
      this.$randMax.prop('disabled', true);
      this.$submit.prop('disabled', true);
      this.$submit.text('Loading...');
      this.busy = true;
    }
    return this;
  };
  Writer.validateForm = function() {
    var isValid;
    isValid = true;
    if (!this.validateNRows()) {
      isValid = false;
    }
    if (!this.validateRandMax()) {
      isValid = false;
    }
    return isValid;
  };
  Writer.validateNRows = function() {
    var max, min, val;
    min = 1;
    max = 100;
    val = this.$nRows.val();
    val = parseInt(val * 1);
    if (isNaN(val) || (!isNaN(val) && (val <= min || val >= max))) {
      this.$nRows.val(this.nRowsDefault);
      this.model.n_rows = this.nRowsDefault;
      return false;
    } else {
      this.$nRows.val(val);
      this.model.n_rows = val;
      return true;
    }
  };
  Writer.validateRandMax = function() {
    var max, min, val;
    min = 1;
    max = 100;
    val = this.$randMax.val();
    val = parseFloat(val * 1);
    if (isNaN(val) || (!isNaN(val) && (val <= min || val >= max))) {
      this.$randMax.val(this.randMaxDefault);
      this.model.rand_max = this.randMaxDefault;
      return false;
    } else {
      this.model.rand_max = val;
      return true;
    }
  };
  Reader.busy = false;
  Reader.initialize = function() {
    this.$fileInput = $("input[name='files[]']");
    this.$dropZone = $('#filedrop');
    this.$message = $('#js-reader-message');
    return this.initFileUpload();
  };
  Reader.initFileUpload = function() {
    var opts,
      _this = this;
    opts = {
      url: '/api/read/demo',
      dataType: 'json',
      dropZone: this.$dropZone,
      add: function(e, data) {
        if (data.files[0].name.match(/\.xlsx$/)) {
          _this.toggleBusy();
          _this.$message.html("");
          return data.submit();
        } else {
          return _this.$message.html(messages.wrongFileType);
        }
      },
      done: function(e, data) {
        return _this.$message.html(messages.readerResult(data.result));
      },
      fail: function() {
        return _this.$message.html(messages.error);
      },
      always: function() {
        return _this.toggleBusy();
      }
    };
    $('#fileupload').fileupload(opts);
    $(document).bind('drop dragover', function(e) {
      return e.preventDefault();
    });
    this.$dropZone.on('dragover', function(e) {
      return _this.$dropZone.addClass('hover');
    });
    this.$dropZone.on('dragleave', function(e) {
      return _this.$dropZone.removeClass('hover');
    });
    return this.$dropZone.on('drop', function(e) {
      return _this.$dropZone.removeClass('hover');
    });
  };
  Reader.toggleBusy = function() {
    if (this.busy) {
      this.$fileInput.prop('disabled', false);
      this.$dropZone.removeClass('disabled');
      this.$dropZone.text('Or drop file here');
      this.busy = false;
    } else {
      this.$fileInput.prop('disabled', true);
      this.$dropZone.addClass('disabled');
      this.$dropZone.text('Loading');
      this.busy = true;
    }
    return this;
  };
  return $(function() {
    App.initialize();
    return window.App = App;
  });
})(jQuery);
