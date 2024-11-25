// Get the button and file input element
const chooseImageButton = document.getElementById('chooseImageButton');
const fileInput = document.getElementById('fileInput');

// When the button is clicked, trigger the file input click
chooseImageButton.addEventListener('click', () => {
  fileInput.click();
});

