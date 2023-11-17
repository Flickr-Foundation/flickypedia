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
  const errorElement = document.querySelector(`p[for="${inputElement.id}"]`);

  inputElement.addEventListener("blur", function () {

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
    inputElement.classList.add("thinking");

    const originalFormat = inputElement.getAttribute("data-originalformat");
    const title = `File:${inputElement.value}.${originalFormat}`;

    fetch(`/api/validate_title?title=${title}`)
      .then((response) => response.json())
      .then(function (json) {

        /* The response from the API should be of the form
         *
         *    {"result": "ok"} or
         *    {"result": "duplicate", "text": "…"}
         *
         * The text is suitable for display in the UI.
         */
        if (json.result === "ok") {
          errorElement.classList.add("hidden");
          inputElement.setCustomValidity("");
        } else {
          errorElement.innerHTML = json.text;
          errorElement.classList.remove("hidden");
          inputElement.setCustomValidity(json.text.split(".")[0]);
        }

        /* We're done thinking! */
        inputElement.classList.remove("thinking");
      });
  });
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
      counterElement.innerHTML =
        "<span class=\"remainingCharacters\">No</span> characters left";
    } else if (remainingCharacters === 1) {
      counterElement.innerHTML =
        "<span class=\"remainingCharacters\">1</span> character left";
    } else if (remainingCharacters > 1) {
      counterElement.innerHTML =
        `<span class="remainingCharacters">${remainingCharacters}</span>` +
        " characters left";
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

  inputElement.addEventListener("input", () => updateCharCounter());
  inputElement.addEventListener("focus", () => updateCharCounter());
}

/*
 * Add interactive categories.
 *
 * We hide the <textarea> and insert an <input> field that will have
 * an associated autocomplete function.
 */
function addInteractiveCategoriesTo(categoriesElement, parentForm) {
  const textAreaElement = categoriesElement.querySelector("textarea");

  /* Hide the original <textarea> */
  textAreaElement.style.display = "none";

  /* Create a new inputElement where the user can enter one category
   * at a time.  Next to the inputElement is a "+" button. */
  const categoryInputs = document.createElement("div");
  categoryInputs.classList.add("category_inputs");

  const autocompleteContainer = document.createElement("div");
  autocompleteContainer.classList.add("autocomplete");

  const inputElement = document.createElement("input");
  inputElement.type = "text";

  autocompleteContainer.appendChild(inputElement);
  categoryInputs.appendChild(autocompleteContainer);

  /* Create a button that a user can click to add a new category. */
  const addCategoryButton = document.createElement("input");
  addCategoryButton.type = "button";
  addCategoryButton.value = "+";
  addCategoryButton.classList.add("pink_button");
  addCategoryButton.onclick = function (event) {
    addCategory();
    event.preventDefault();
  };
  categoryInputs.appendChild(addCategoryButton);

  textAreaElement.after(categoryInputs);

  /* Create a visible <ul> element where we can show the user the list
   * of categories they've selected.
   */
  const listOfCategories = document.createElement("ul");
  listOfCategories.classList.add("selected_categories");
  categoryInputs.after(listOfCategories);

  /* Add a category based on the current contents of this input element. */
  function addCategory() {
    const newCategory = inputElement.value;

    if (newCategory === "") {
      return;
    }

    /* Add it to the hidden <textarea> */
    textAreaElement.value += `${newCategory}\n`;

    /* Add it to the list of categories shown in the UI.
     *
     * This will show the name of the category and an [X] button to remove it.
     */
    const listEntry = document.createElement("li");

    const span = document.createElement("span");
    span.innerHTML = newCategory;
    listEntry.appendChild(span);

    const removeCategoryButton = document.createElement("a");
    removeCategoryButton.innerHTML = "[x]";
    removeCategoryButton.classList.add("remove_category");
    removeCategoryButton.onclick = function () {
      removeCategory(newCategory, listEntry);
    };
    listEntry.appendChild(removeCategoryButton);

    listOfCategories.appendChild(listEntry);

    /* Clear the <input> element */
    inputElement.value = "";
  }

  /* Remove a category from the selected list. */
  function removeCategory(categoryName, listEntryElement) {

    /* Remove the category name from the <textarea> */
    textAreaElement.value =
      textAreaElement.value
        .split("\n")
        .filter((category) => category !== categoryName)
        .join("\n");

    /* Remove the category from the list of categories shown to the user */
    listEntryElement.remove();
  }

  /* If somebody presses 'enter' in this field, add a category rather
   * than submitting the form. */
  inputElement.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
      addCategory();
      event.preventDefault();
    }
  });

  /* If somebody pastes into this field, split on newlines and add those
   * categories. */
  inputElement.addEventListener("paste", function (event) {
    const clipboard = (event.clipboardData || window.clipboardData);
    const categories = clipboard.getData("text").split("\n");

    categories.forEach(function (category) {
      inputElement.value = category;
      addCategory();
    });

    /* The default action is to insert the text into the <input>, but
     * we don't want that here -- we want the user to have an empty
     * field for more inputs. */
    event.preventDefault();
  });

  /* If the user clicks the "Upload" button, add anything in the <input>
   * which they haven't explicitly added to the list of categories.
   */
  parentForm.addEventListener("submit", () => addCategory());

  /* As somebody starts typing in this form, query the Wikimedia API
   * and offer an autocomplete menu for categories.
   *
   * This is loosely based on code from
   * https://www.w3schools.com/howto/howto_js_autocomplete.asp
   */
  var currentFocus = -1;

  /* When somebody starts typing or switches to this field, open
   * the autocomplete menu. */
  inputElement.addEventListener("input", () => openAutocompleteMenu());
  inputElement.addEventListener("focus", () => openAutocompleteMenu());

  /* When somebody switches or clicks away from the input, close the
   * autocomplete menu -- unless they clicked on an autocomplete suggestion,
   * in which case apply that first. */
  inputElement.addEventListener("blur", function(event) {
    if (event.relatedTarget !== null &&
        event.relatedTarget.classList.contains("suggestion")) {
      inputElement.value = event.relatedTarget.innerHTML;
    }

    closeAutocompleteMenus();
  });

  /* An attempt to disable browser autocomplete from interfering. */
  inputElement.autocomplete = "off";

  /* Open the autocomplete menu -- query the Flickypedia API to get a
   * list of category suggestions, then put them in a list. */
  function openAutocompleteMenu() {
    closeAutocompleteMenus();

    if (inputElement.value === "") {
      return;
    }

    currentFocus = -1;

    inputElement.classList.add("thinking");

    const autocompleteElement = document.createElement("div");
    autocompleteElement.classList.add("autocomplete-items");

    autocompleteContainer.appendChild(autocompleteElement);

    fetch(`/api/find_matching_categories?query=${inputElement.value}`)
      .then((response) => response.json())
      .then(function (json) {
        for (i = 0; i < json.length; i++) {
          var suggestion = json[i];
          const suggestionElement = document.createElement("div");
          suggestionElement.classList.add("suggestion");
          suggestionElement.innerHTML = suggestion;

          /* This allows the element to receive focus.
           *
           * In turn, when the blur event fires on the 'input' element
           * (somebody has clicked elsewhere), we can detect if:
           *
           *    - they clicked on this suggestion, in which case we should
           *      apply it, or
           *    - they clicked somewhere else, in which case we should just
           *      close the autocomplete menu.
           */
          suggestionElement.tabIndex = "-1";

          autocompleteElement.appendChild(suggestionElement);
        }

        inputElement.classList.remove("thinking");
      });
  }

  inputElement.addEventListener("keydown", function(event) {
    console.log(event.key);

    if (event.key === "ArrowDown") {
      currentFocus++;
      updateFocusedItem();
    } else if (event.key === "ArrowUp") {
      currentFocus--;
      updateFocusedItem();
    } else if (event.key === "Enter") {
      if (currentFocus > -1) {

        inputElement.value =
          autocompleteContainer
            .querySelector(".autocomplete-items")
            .children[currentFocus]
            .innerHTML;

        addCategory();

        closeAutocompleteMenus();
        event.preventDefault();
      }
    } else if (event.key === "Escape") {
      closeAutocompleteMenus();
    }
  });

  function updateFocusedItem() {
    const items =
      autocompleteContainer
        .querySelector(".autocomplete-items")
        .children;

    for (var i = 0; i < items.length; i++) {
      if (i === currentFocus) {
        items[i].classList.add("autocomplete-active");
      } else {
        items[i].classList.remove("autocomplete-active");
      }
    }
  }

  function closeAutocompleteMenus() {
    currentFocus = -1;
    document
      .querySelectorAll(".autocomplete-items")
      .forEach((item) => item.remove());
  }
}

/*
 * Update the state of currently-being-uploaded photos.
 *
 * This function is called once per second on the "wait for upload"
 * screen.  It adds the "Done" or "Not Done" labels to photos.
 */
function updatePhotosWithUploadProgress() {
  fetch(`${window.location}/status`)
    .then((response) => response.json())
    .then(function (json) {
      var processingCount = 0;

      /* If we're done, redirect the user to the next screen. */
      if (json.ready) {
        window.location.href = window.location.href.replace("/wait_for_upload/", "/upload_complete/")
      }

      json.progress.forEach((progress) => {
        const photoId = progress.req.photo.id;
        const uploadStatus = progress.status;

        const liElement = document
          .querySelector(`li[data-id="${photoId}"]`);

        /* If the status has changed, add it to the <li> element for
         * this photo.  Also add the text label if necessary.
         */
        if (liElement.getAttribute("data-status") !== uploadStatus) {
          liElement.setAttribute("data-status", uploadStatus);

          if (uploadStatus === "succeeded") {
            const textElement = document.createElement("div");
            textElement.classList.add("text");
            textElement.innerHTML = "DONE";
            liElement.querySelector('.container').appendChild(textElement);
          }

          if (uploadStatus === "failed") {
            const textElement = document.createElement("div");
            textElement.classList.add("text");
            textElement.innerHTML = "NOT DONE";
            liElement.querySelector('.container').appendChild(textElement);
          }
        }

        if (uploadStatus !== "waiting") {
          processingCount += 1;
        }
      });

      document
        .querySelector('.image_counter')
        .innerHTML = `${processingCount} of ${json.progress.length}`;
    });
}