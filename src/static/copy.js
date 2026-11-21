// Copies the text of the element named in data-copy-target to the clipboard.
(function () {
  const button = document.getElementById("copy");
  if (!button) {
    return;
  }

  const target = document.getElementById(button.dataset.copyTarget);
  const originalLabel = button.textContent;

  function copyWithSelection(text) {
    // for browsers and pages (plain http) without the clipboard API
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const copied = document.execCommand("copy");
    document.body.removeChild(area);
    return copied ? Promise.resolve() : Promise.reject(new Error("copy failed"));
  }

  function copy(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).catch(function () {
        return copyWithSelection(text);
      });
    }
    return copyWithSelection(text);
  }

  function showLabel(label) {
    button.textContent = label;
    window.setTimeout(function () {
      button.textContent = originalLabel;
    }, 2000);
  }

  button.addEventListener("click", function () {
    copy(target.textContent).then(
      function () { showLabel("copied"); },
      function () { showLabel("copy failed"); }
    );
  });
})();
