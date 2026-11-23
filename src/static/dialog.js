// Shows the dialog about an existing identical reference as a modal dialog:
// the page behind it cannot be used until add/save or cancel is chosen.
// Without JavaScript the dialog is still visible (it is rendered open).
(function () {
  const dialog = document.getElementById("duplicate-dialog");
  if (!dialog || typeof dialog.showModal !== "function") {
    return;
  }
  dialog.close();
  dialog.showModal();
  // the dialog itself has the focus, so neither button looks selected;
  // Tab moves to the buttons and Esc closes the dialog
  dialog.focus();
})();
