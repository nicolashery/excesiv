
(function($) {
  var App, Reader, Writer, messages;
  App = {};
  Writer = App.Writer = {};
  Reader = App.Reader = {};
  messages = App.messages = {
    error: '<span class="error">Oops! An error occured. Please try <a href="/">refreshing</a> the page.</span>',
    download: function(fileUrl) {
      return "<a href='" + fileUrl + "'>Download Excel file</a>";
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
          return _this.$message.html(messages.download(data.file_url));
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
  Reader.initialize = function() {};
  Reader.toggleBusy = function() {
    if (this.busy) {
      this.busy = false;
    } else {
      this.busy = true;
    }
    return this;
  };
  return $(function() {
    App.initialize();
    return window.App = App;
  });
})(jQuery);
