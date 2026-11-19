const galleryGrid = document.getElementById('gallery-sortable');
const orderForm = document.getElementById('gallery-order-form');
let draggedPhoto;

if (galleryGrid && orderForm) {
  galleryGrid.addEventListener('dragstart', event => {
    if (event.target.closest('a, button, input, form')) {
      event.preventDefault();
      return;
    }
    draggedPhoto = event.target.closest('[data-photo-id]');
    if (!draggedPhoto) return;
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', draggedPhoto.dataset.photoId);
    draggedPhoto.classList.add('gallery-dragging');
  });
  galleryGrid.addEventListener('dragover', event => {
    if (!draggedPhoto) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  });
  galleryGrid.addEventListener('drop', event => {
    if (!draggedPhoto) return;
    event.preventDefault();
    const target = event.target.closest('[data-photo-id]');
    if (target && target !== draggedPhoto) {
      const items = Array.from(galleryGrid.children);
      const next = items.indexOf(draggedPhoto) < items.indexOf(target) ? target.nextSibling : target;
      galleryGrid.insertBefore(draggedPhoto, next);
      document.getElementById('gallery-order').value = JSON.stringify(
        Array.from(galleryGrid.querySelectorAll('[data-photo-id]'), item => Number(item.dataset.photoId))
      );
      orderForm.requestSubmit();
    }
  });
  galleryGrid.addEventListener('dragend', () => {
    draggedPhoto?.classList.remove('gallery-dragging');
    draggedPhoto = undefined;
  });
}
