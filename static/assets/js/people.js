document.querySelectorAll('.delete-form').forEach(form => {
  form.addEventListener('submit', event => {
    if (!window.confirm('Remove this employee and their photo from the team page?')) event.preventDefault();
  });
});
const photoInput = document.getElementById('photo');
const preview = document.getElementById('photo-preview');
const originalPreview = preview ? Array.from(preview.childNodes, node => node.cloneNode(true)) : [];
let previewUrl;
photoInput?.addEventListener('change', () => {
  photoInput.setCustomValidity('');
  const file = photoInput.files[0];
  if (!file) {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    preview.replaceChildren(...originalPreview.map(node => node.cloneNode(true)));
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    photoInput.setCustomValidity('Choose a photo smaller than 5 MB.');
    photoInput.reportValidity();
    return;
  }
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  const image = document.createElement('img');
  image.src = previewUrl;
  image.alt = 'Preview of selected employee photo';
  preview.replaceChildren(image);
});
