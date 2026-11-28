// The "more" menu of the reference type choice: closes after a type is chosen
// and shows the chosen type in place of the word more. Clicking outside the
// menu or pressing Esc closes it. Without JavaScript the menu still works,
// it just stays open until it is clicked again.
(function () {
  const menu = document.getElementById("type-more");
  if (!menu) {
    return;
  }
  const summary = menu.querySelector("summary");
  const label = menu.querySelector(".type-more-label");
  const fieldset = menu.closest("fieldset");

  fieldset.querySelectorAll('input[type="radio"]').forEach(function (radio) {
    radio.addEventListener("change", function () {
      label.textContent = menu.contains(radio) ? radio.value : "more";
      if (menu.contains(radio)) {
        menu.open = false;
        summary.focus();
      }
    });
  });

  document.addEventListener("click", function (event) {
    if (menu.open && !menu.contains(event.target)) {
      menu.open = false;
    }
  });

  menu.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && menu.open) {
      event.preventDefault();
      menu.open = false;
      summary.focus();
    }
  });
})();
