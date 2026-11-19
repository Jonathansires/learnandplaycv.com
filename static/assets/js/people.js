document.querySelectorAll('.delete-form').forEach(form => {
  form.addEventListener('submit', event => {
    if (!window.confirm(form.dataset.confirm || 'Remove this employee and their photo from the team page?')) event.preventDefault();
  });
});

const photoInput = document.getElementById('photo');
const preview = document.getElementById('photo-preview');
const photoStatus = document.getElementById('photo-status');
const originalPreview = preview ? Array.from(preview.childNodes, node => node.cloneNode(true)) : [];
const photoForm = photoInput?.form;
const saveButtons = photoForm ? Array.from(photoForm.querySelectorAll('button[type="submit"]')) : [];
let selection = 0;
let processing = false;
let previewUrl;

function setProcessing(busy) {
  processing = busy;
  saveButtons.forEach(button => { button.disabled = busy; });
  photoInput.setAttribute('aria-busy', String(busy));
}

function photoSize(bytes) {
  return bytes >= 1024 * 1024 ? `${(bytes / (1024 * 1024)).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

async function compressPhoto(file) {
  const sourceUrl = URL.createObjectURL(file);
  try {
    const image = new Image();
    await new Promise((resolve, reject) => {
      image.onload = resolve;
      image.onerror = () => reject(new Error('This photo could not be opened. Try a JPG, PNG, or WebP photo.'));
      image.src = sourceUrl;
    });
    const scale = Math.min(1, 1200 / Math.max(image.naturalWidth, image.naturalHeight));
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Your browser could not prepare this photo. Try another browser.');
    // Stay below common reverse-proxy upload limits, including multipart overhead.
    const targetBytes = 450 * 1024;
    for (const reduction of [1, 0.8, 0.64, 0.512]) {
      canvas.width = Math.max(1, Math.round(image.naturalWidth * scale * reduction));
      canvas.height = Math.max(1, Math.round(image.naturalHeight * scale * reduction));
      // JPEG needs a solid background for transparent PNG and WebP uploads.
      context.fillStyle = '#ffffff';
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      for (const quality of [0.86, 0.74, 0.62]) {
        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', quality));
        if (!blob) throw new Error('Your browser could not prepare this photo. Please try a different photo.');
        if (blob.size <= targetBytes) {
          const name = file.name.replace(/\.[^.]+$/, '') || 'employee';
          return new File([blob], `${name}.jpg`, { type: 'image/jpeg', lastModified: Date.now() });
        }
      }
    }
    throw new Error('This photo could not be compressed enough. Please try a different photo.');
  } finally {
    URL.revokeObjectURL(sourceUrl);
  }
}

photoForm?.addEventListener('submit', event => {
  if (processing) event.preventDefault();
});

photoInput?.addEventListener('change', async () => {
  const currentSelection = ++selection;
  photoInput.setCustomValidity('');
  const file = photoInput.files[0];
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
    previewUrl = undefined;
  }
  if (!file) {
    setProcessing(false);
    photoStatus.textContent = '';
    preview.replaceChildren(...originalPreview.map(node => node.cloneNode(true)));
    return;
  }
  setProcessing(true);
  photoInput.setCustomValidity('Please wait while your photo is prepared.');
  photoStatus.textContent = 'Preparing your photo for the web…';
  try {
    const prepared = await compressPhoto(file);
    if (currentSelection !== selection) return;
    const transfer = new DataTransfer();
    transfer.items.add(prepared);
    photoInput.files = transfer.files;
    previewUrl = URL.createObjectURL(prepared);
    const image = document.createElement('img');
    image.src = previewUrl;
    image.alt = 'Preview of the prepared photo';
    preview.replaceChildren(image);
    photoInput.setCustomValidity('');
    photoStatus.textContent = `Photo ready: ${photoSize(prepared.size)} (original ${photoSize(file.size)}).`;
  } catch (error) {
    if (currentSelection !== selection) return;
    photoInput.setCustomValidity(error.message);
    photoStatus.textContent = error.message;
    photoInput.reportValidity();
  } finally {
    if (currentSelection === selection) setProcessing(false);
  }
});
