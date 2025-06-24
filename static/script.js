function toggleInput(checkbox) {
  const input = checkbox.nextElementSibling;
  if (checkbox.checked) {
    input.style.display = "inline-block";
  } else {
    input.style.display = "none";
    input.value = "";
  }
}
