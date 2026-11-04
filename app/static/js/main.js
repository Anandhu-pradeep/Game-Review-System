/**
 * GameShelf – Interactive UI Components & Client Features
 */

document.addEventListener('DOMContentLoaded', () => {
  initStarRatings();
  initLikeButtons();
  initWishlistButtons();
  initConfirmModals();
  initFileUploadDropzones();
  initKeyboardShortcuts();
});

// Retrieve CSRF token from meta tag
function getCSRFToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

// Toast notification helper
function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container-custom');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container-custom';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'toast-custom';
  
  let iconClass = 'bi-check-circle-fill text-success';
  if (type === 'danger' || type === 'error') iconClass = 'bi-exclamation-triangle-fill text-danger';
  if (type === 'warning') iconClass = 'bi-exclamation-circle-fill text-warning';
  if (type === 'info') iconClass = 'bi-info-circle-fill text-info';

  toast.innerHTML = `
    <i class="bi ${iconClass} fs-5"></i>
    <div class="flex-grow-1 small fw-medium">${message}</div>
    <button type="button" class="btn-close btn-close-white" aria-label="Close" style="font-size: 0.75rem;"></button>
  `;

  toast.querySelector('.btn-close').addEventListener('click', () => {
    toast.remove();
  });

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 350);
  }, 4000);
}

// Interactive Star Rating Component
function initStarRatings() {
  const widgets = document.querySelectorAll('.star-rating-box');

  widgets.forEach(widget => {
    const gameId = widget.getAttribute('data-game-id');
    const stars = widget.querySelectorAll('.star-icon');
    let currentScore = parseInt(widget.getAttribute('data-current-score') || '0');

    function renderStars(score) {
      stars.forEach(star => {
        const val = parseInt(star.getAttribute('data-value'));
        if (val <= score) {
          star.classList.remove('bi-star');
          star.classList.add('bi-star-fill', 'active');
        } else {
          star.classList.remove('bi-star-fill', 'active');
          star.classList.add('bi-star');
        }
      });
    }

    renderStars(currentScore);

    stars.forEach(star => {
      star.addEventListener('mouseenter', () => {
        const hoverVal = parseInt(star.getAttribute('data-value'));
        renderStars(hoverVal);
      });

      star.addEventListener('mouseleave', () => {
        renderStars(currentScore);
      });

      star.addEventListener('click', async () => {
        const chosenScore = parseInt(star.getAttribute('data-value'));

        if (gameId) {
          try {
            const formData = new FormData();
            formData.append('score', chosenScore);
            formData.append('csrf_token', getCSRFToken());

            const res = await fetch(`/games/${gameId}/rate`, {
              method: 'POST',
              headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken()
              },
              body: formData
            });

            const data = await res.json();
            if (data.success) {
              currentScore = chosenScore;
              widget.setAttribute('data-current-score', currentScore);
              renderStars(currentScore);
              showToast(data.message, 'success');

              const avgElem = document.querySelector('#game-avg-rating');
              const totalElem = document.querySelector('#game-total-ratings');
              if (avgElem) avgElem.innerText = data.average_rating.toFixed(1);
              if (totalElem) totalElem.innerText = `(${data.total_ratings} ratings)`;
            } else {
              showToast(data.message || 'Error saving rating', 'danger');
            }
          } catch (err) {
            console.error(err);
            showToast('Failed to submit rating. Please try again.', 'danger');
          }
        }
      });
    });
  });
}

// Like Button Interactive Toggle
function initLikeButtons() {
  document.querySelectorAll('.btn-like-toggle').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const gameId = btn.getAttribute('data-game-id');
      if (!gameId) return;

      try {
        const res = await fetch(`/games/${gameId}/like`, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
          }
        });

        if (res.status === 401 || res.redirected) {
          window.location.href = '/login';
          return;
        }

        const data = await res.json();
        if (data.success) {
          const icon = btn.querySelector('i');
          const countSpan = btn.querySelector('.like-count');

          if (data.liked) {
            btn.classList.add('active', 'btn-danger');
            btn.classList.remove('btn-secondary-gaming');
            if (icon) {
              icon.classList.remove('bi-heart');
              icon.classList.add('bi-heart-fill');
            }
          } else {
            btn.classList.remove('active', 'btn-danger');
            btn.classList.add('btn-secondary-gaming');
            if (icon) {
              icon.classList.remove('bi-heart-fill');
              icon.classList.add('bi-heart');
            }
          }

          if (countSpan) {
            countSpan.innerText = data.likes_count;
          }

          showToast(data.message, 'info');
        }
      } catch (err) {
        console.error(err);
        showToast('Error updating like.', 'danger');
      }
    });
  });
}

// Wishlist Button Interactive Toggle
function initWishlistButtons() {
  document.querySelectorAll('.btn-wishlist-toggle').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const gameId = btn.getAttribute('data-game-id');
      if (!gameId) return;

      try {
        const res = await fetch(`/games/${gameId}/wishlist`, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
          }
        });

        if (res.status === 401 || res.redirected) {
          window.location.href = '/login';
          return;
        }

        const data = await res.json();
        if (data.success) {
          const icon = btn.querySelector('i');
          const textSpan = btn.querySelector('.wishlist-text');

          if (data.in_wishlist) {
            btn.classList.add('btn-primary-gaming');
            btn.classList.remove('btn-secondary-gaming');
            if (icon) {
              icon.classList.remove('bi-bookmark');
              icon.classList.add('bi-bookmark-fill');
            }
            if (textSpan) textSpan.innerText = 'In Wishlist';
          } else {
            btn.classList.remove('btn-primary-gaming');
            btn.classList.add('btn-secondary-gaming');
            if (icon) {
              icon.classList.remove('bi-bookmark-fill');
              icon.classList.add('bi-bookmark');
            }
            if (textSpan) textSpan.innerText = 'Add to Wishlist';
          }

          showToast(data.message, 'info');
        }
      } catch (err) {
        console.error(err);
        showToast('Error updating wishlist.', 'danger');
      }
    });
  });
}

// Confirmation Modals
function initConfirmModals() {
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', (e) => {
      const msg = el.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });
}

// Drag & Drop File Upload Zones
function initFileUploadDropzones() {
  document.querySelectorAll('.dropzone-upload-box').forEach(zone => {
    const fileInput = zone.querySelector('input[type="file"]');
    const previewContainer = zone.querySelector('.dropzone-preview');

    if (!fileInput) return;

    zone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(name => {
      zone.addEventListener(name, (e) => {
        e.preventDefault();
        zone.classList.add('border-primary');
      });
    });

    ['dragleave', 'drop'].forEach(name => {
      zone.addEventListener(name, (e) => {
        e.preventDefault();
        zone.classList.remove('border-primary');
      });
    });

    zone.addEventListener('drop', (e) => {
      if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelect(fileInput.files[0], previewContainer);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length) {
        handleFileSelect(fileInput.files[0], previewContainer);
      }
    });
  });

  function handleFileSelect(file, previewContainer) {
    if (!file || !previewContainer) return;
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        previewContainer.innerHTML = `<img src="${e.target.result}" class="rounded shadow mt-2" style="max-height: 140px; object-fit: cover;">`;
      };
      reader.readAsDataURL(file);
    }
  }
}

// Keyboard shortcut: '/' focuses global search bar
function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      e.preventDefault();
      const searchInput = document.querySelector('.nav-search-input');
      if (searchInput) {
        searchInput.focus();
      }
    }
  });
}
