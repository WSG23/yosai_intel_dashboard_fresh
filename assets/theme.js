(function () {
  function syncDropdown() {
    var dropdown = document.getElementById('theme-dropdown');
    if (!dropdown) return;
    var current = document.documentElement.dataset.theme || 'dark';
    if (dropdown.value !== current) {
      dropdown.value = current;
    }
    if (!dropdown.__bound) {
      dropdown.addEventListener('change', function (e) {
        if (window.setAppTheme) {
          window.setAppTheme(e.target.value);
        }
      });
      dropdown.__bound = true;
    }
  }

  document.addEventListener('DOMContentLoaded', syncDropdown);
  document.addEventListener('themeChange', syncDropdown);
  syncDropdown();
})();
