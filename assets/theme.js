(function () {
  function syncDropdown() {
    var dropdown = document.getElementById('theme-dropdown');
    if (!dropdown) return;
    var html = document.documentElement;
    var current = 'dark';
    if (html.classList.contains('light-mode')) current = 'light';
    else if (html.classList.contains('high-contrast-mode')) current = 'high-contrast';
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
