// Selecting references on the list for deleting them at once or for a .bib file.
// The delete and create .bib buttons are disabled (grey) while no reference is
// selected, and the browser asks for a confirmation before deleting.
// Select all selects every reference, or unselects them when all are selected.
(function () {
  const form = document.getElementById("delete-selected-form");
  const button = document.getElementById("delete-selected");
  const selectAll = document.getElementById("select-all");
  const createBib = document.getElementById("create-bib");
  if (!form || !button || !selectAll || !createBib) {
    return;
  }

  function checkboxes() {
    return document.querySelectorAll('input[name="reference_id"]');
  }

  function selectedCount() {
    return document.querySelectorAll('input[name="reference_id"]:checked').length;
  }

  function allSelected() {
    const count = checkboxes().length;
    return count > 0 && selectedCount() === count;
  }

  function update() {
    button.disabled = selectedCount() === 0;
    createBib.disabled = selectedCount() === 0;
    selectAll.textContent = allSelected() ? "unselect" : "select all";
    // nothing to select when the search found nothing
    selectAll.disabled = checkboxes().length === 0;
  }

  selectAll.addEventListener("click", () => {
    const select = !allSelected();
    checkboxes().forEach((checkbox) => {
      checkbox.checked = select;
    });
    update();
  });

  document.addEventListener("change", (event) => {
    if (event.target.name === "reference_id") {
      update();
    }
  });

  form.addEventListener("submit", (event) => {
    if (event.submitter === createBib) {
      // the .bib file is downloaded and the list stays as it is
      return;
    }
    const count = selectedCount();
    const message = count === 1 ? "Delete 1 reference?" : `Delete ${count} references?`;
    if (count === 0 || !confirm(message)) {
      event.preventDefault();
    }
  });

  // the browser may keep the checkboxes selected when going back to the page
  update();
})();
