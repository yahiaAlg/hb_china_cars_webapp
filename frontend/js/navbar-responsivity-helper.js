// Ensure proper navbar element ordering on all screen sizes
document.addEventListener("DOMContentLoaded", function () {
  const navbar = document.querySelector(".navbar");
  const logo = navbar.querySelector(".logo");
  const adminDropdown = navbar.querySelector(".navbar-admin");
  const mobileMenuBtn = navbar.querySelector("#mobileMenuBtn");

  // Force correct order
  function fixNavbarOrder() {
    if (logo && mobileMenuBtn) {
      navbar.appendChild(logo);
      if (adminDropdown) {
        navbar.appendChild(adminDropdown);
      }
      navbar.appendChild(mobileMenuBtn);
    }
  }

  // Apply fix on load and resize
  fixNavbarOrder();
  window.addEventListener("resize", fixNavbarOrder);
});
