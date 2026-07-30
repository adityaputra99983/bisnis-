(function() {
  'use strict';

  window.ImageCompressor = {
    MAX_DIMENSION: 1920,
    QUALITY: 0.85,
    MAX_SIZE_BEFORE_COMPRESS: 1 * 1024 * 1024,
  };

  ImageCompressor.compress = function(file) {
    return new Promise(function(resolve, reject) {
      if (!file || !file.type.startsWith('image/')) {
        resolve(file);
        return;
      }
      if (file.size <= ImageCompressor.MAX_SIZE_BEFORE_COMPRESS) {
        resolve(file);
        return;
      }

      var reader = new FileReader();
      reader.onload = function(e) {
        var img = new Image();
        img.onload = function() {
          var w = img.width, h = img.height;
          var max = ImageCompressor.MAX_DIMENSION;
          if (w > max || h > max) {
            if (w > h) { h = h * max / w; w = max; }
            else { w = w * max / h; h = max; }
          }
          var canvas = document.createElement('canvas');
          canvas.width = Math.round(w);
          canvas.height = Math.round(h);
          var ctx = canvas.getContext('2d');
          ctx.imageSmoothingEnabled = true;
          ctx.imageSmoothingQuality = 'high';
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          var ext = file.name.split('.').pop().toLowerCase();
          var mimeType = (ext === 'png') ? 'image/png' : 'image/webp';
          var quality = (ext === 'png') ? undefined : ImageCompressor.QUALITY;
          canvas.toBlob(function(blob) {
            if (!blob) { resolve(file); return; }
            var compressed = new File([blob], file.name.replace(/\.[^.]+$/, '.webp'), {
              type: blob.type || 'image/webp',
              lastModified: Date.now()
            });
            resolve(compressed);
          }, mimeType, quality);
        };
        img.onerror = function() { resolve(file); };
        img.src = e.target.result;
      };
      reader.onerror = function() { resolve(file); };
      reader.readAsDataURL(file);
    });
  };

  ImageCompressor.setupForm = function(formSelector, inputSelector, previewCallback) {
    var form = (typeof formSelector === 'string') ? document.querySelector(formSelector) : formSelector;
    var input = (typeof inputSelector === 'string') ? document.querySelector(inputSelector) : inputSelector;
    if (!form || !input) return;

    var isCompressing = false;

    form.addEventListener('submit', function(e) {
      if (isCompressing) return;
      var files = input.files;
      if (!files || files.length === 0) return;

      var file = files[0];
      if (file.size <= ImageCompressor.MAX_SIZE_BEFORE_COMPRESS) return;

      e.preventDefault();
      isCompressing = true;

      var submitBtn = form.querySelector('[type="submit"]');
      if (submitBtn) submitBtn.disabled = true;

      ImageCompressor.compress(file).then(function(compressed) {
        if (compressed !== file) {
          var dt = new DataTransfer();
          dt.items.add(compressed);
          input.files = dt.files;
          if (previewCallback) previewCallback(compressed);
        }
        isCompressing = false;
        if (submitBtn) submitBtn.disabled = false;
        form.submit();
      }).catch(function() {
        isCompressing = false;
        if (submitBtn) submitBtn.disabled = false;
        form.submit();
      });
    });
  };
})();
