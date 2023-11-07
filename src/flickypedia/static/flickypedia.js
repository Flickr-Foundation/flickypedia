/*
 * Add a title validator to an input field.
 *
 * When the user finishes typing in the field and clicks away (which
 * gives us a 'blur' event), we check their title against the
 * Wikimedia APIs, e.g. whether the title is a duplicate, too long,
 * has forbidden characters.
 *
 * If the title is rejected, we add visible red text below the box
 * and a validation prompt, so the form can't be submitted.
 */
function addTitleValidatorTo(inputElement) {
  const errorElement = document
    .querySelector(`p[for="${inputElement.id}"]`);

  inputElement.addEventListener("blur", () => {

    /* If the user hasn't entered anything, just clear any validation --
     * it'll get picked up by other validation that marks the field as
     * required and having a min/max length.
     */
    if (inputElement.value === "") {
      errorElement.innerHTML = "";
      inputElement.setCustomValidity("");
      return;
    }

    /* Label the class as thinking; this adds a progress indicator
     * to the UI (see the CSS for inputElement.thinking) */
    inputElement.classList.add("thinking")

    const title = `File:${inputElement.value}.${inputElement.getAttribute("data-originalformat")}`;

    fetch(`/api/validate_title?title=${title}`)
      .then((response) => response.json())
      .then((json) => {

        /* The response from the API should be of the form
         *
         *    {"result": "ok"} or
         *    {"result": "duplicate", "text": "…"}
         *
         * The text is suitable for display in the UI.
         */
        if (json.result === 'ok') {
          errorElement.classList.add("hidden");
          inputElement.setCustomValidity("");
        } else {
          errorElement.innerHTML = json.text;
          errorElement.classList.remove("hidden");
          inputElement.setCustomValidity(json.text.split(".")[0]);
        }

        /* We're done thinking! */
        inputElement.classList.remove("thinking")
      });
  })
}

/*
 * Add a character counter to an input field.
 *
 * As the user is typing in the field, we'll display a "N characters"
 * remaining indicator to tell them how much they have left.
 */
function addCharCounterTo(inputElement, counterElement) {
  const maxCount = inputElement.getAttribute("maxlength");

  function updateCharCounter() {
    const enteredCharacters = inputElement.value.length;
    const remainingCharacters = maxCount - enteredCharacters;

    if (remainingCharacters === 0) {
      counterElement.innerHTML = '<span class="remainingCharacters">No</span> characters left';
    } else if (remainingCharacters === 1) {
      counterElement.innerHTML = '<span class="remainingCharacters">1</span> character left';
    } else if (remainingCharacters > 1) {
      counterElement.innerHTML = `<span class="remainingCharacters">${remainingCharacters}</span> characters left`;
    } else if (remainingCharacters === -1) {
      counterElement.innerHTML = `
        <span class="too_many_characters">
          <span class="remainingCharacters">1</span>
          character too many
        </span>`;
    } else {
      counterElement.innerHTML = `
        <span class="too_many_characters">
          <span class="remainingCharacters">${Math.abs(remainingCharacters)}</span>
          characters too many
        </span>`;
    }
  }

  /* When the user selected the field, we want to display the counter and
   * keep it updated as they type.
   *
   * When the user switches away from the field, we want to hide the counter
   * if they've entered enough of a caption -- otherwise we keep showing
   * the error message.
   */
  updateCharCounter();

  inputElement.addEventListener("input", () => {
    updateCharCounter();
  });

  inputElement.addEventListener("focus", () => {
    updateCharCounter();
  });
}