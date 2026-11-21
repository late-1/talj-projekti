// Shows the fields of the chosen reference type in the add and edit forms.
// Hidden fields are disabled, so that they are not sent or required.
(function () {
  const form = document.getElementById("reference-form");
  if (!form) {
    return;
  }

  function types(value) {
    return value ? value.split(" ") : [];
  }

  function showFields() {
    const chosen = form.querySelector('input[name="entry_type"]:checked');
    const type = chosen ? chosen.value : "";

    form.querySelectorAll(".field").forEach(function (field) {
      const required = types(field.dataset.requiredFor).includes(type);
      const optional = types(field.dataset.optionalFor).includes(type);
      const input = field.querySelector("input");

      field.hidden = !required && !optional;
      input.disabled = field.hidden;
      input.required = required;
      field.querySelector(".optional-mark").hidden = !optional;
    });
  }

  form.querySelectorAll('input[name="entry_type"]').forEach(function (radio) {
    radio.addEventListener("change", showFields);
  });

  showFields();
})();
