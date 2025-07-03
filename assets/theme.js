(function () {
  function syncDropdown() {
    var dropdown = document.getElementById('theme-dropdown');
    if (!dropdown) return;
    var current = document.documentElement.dataset.theme || 'dark';
    if (dropdown.value !== current) {
      dropdown.value = current;
    }
  }

  document.addEventListener('DOMContentLoaded', syncDropdown);
  document.addEventListener('themeChange', syncDropdown);

  var dropdown = document.getElementById('theme-dropdown');
  if (dropdown) {
    dropdown.addEventListener('change', function (e) {
      if (window.setAppTheme) {
        window.setAppTheme(e.target.value);
      }
    });
  }
})();
