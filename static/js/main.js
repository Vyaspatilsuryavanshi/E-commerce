/**
 * AURA LUXE - Main UI Controller
 * Handles Drawer, Modals, Wishlist, Toast Notifications, and Dynamic Cart Actions
 */

document.addEventListener('DOMContentLoaded', () => {
  initCartDrawer();
  initWishlist();
  initModals();
});

/* ==========================================================================
   Toast Notification System
   ========================================================================== */
function showToast(message, type = 'success') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const messageText = document.createElement('span');
  messageText.textContent = String(message ?? '');
  const closeButton = document.createElement('button');
  closeButton.type = 'button';
  closeButton.textContent = '✕';
  closeButton.setAttribute('aria-label', 'Dismiss notification');
  closeButton.style.cssText = 'font-size:1.1rem; opacity:0.6;';
  closeButton.addEventListener('click', () => toast.remove());
  toast.append(messageText, closeButton);

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(40px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

/* ==========================================================================
   Cart Drawer (Slide-out Mini Bag)
   ========================================================================== */
function initCartDrawer() {
  const drawer = document.getElementById('cartDrawer');
  const backdrop = document.getElementById('drawerBackdrop');
  const openButtons = document.querySelectorAll('.js-open-cart-drawer');
  const closeButtons = document.querySelectorAll('.js-close-cart-drawer');

  if (!drawer) return;

  function openDrawer() {
    refreshCartDrawer();
    drawer.classList.add('open');
    if (backdrop) backdrop.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeDrawer() {
    drawer.classList.remove('open');
    if (backdrop) backdrop.classList.remove('active');
    document.body.style.overflow = '';
  }

  openButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      openDrawer();
    });
  });

  closeButtons.forEach(btn => {
    btn.addEventListener('click', closeDrawer);
  });

  if (backdrop) {
    backdrop.addEventListener('click', closeDrawer);
  }

  // Intercept Ajax Add To Cart forms
  document.addEventListener('submit', (e) => {
    const form = e.target.closest('.js-ajax-add-to-cart');
    if (form) {
      e.preventDefault();
      const formData = new FormData(form);
      const submitBtn = form.querySelector('button[type="submit"]');
      const originalText = submitBtn ? submitBtn.innerHTML : '';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Adding...</span>';
      }

      fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          showToast(data.message, 'success');
          updateCartBadges(data.cart.item_count);
          renderCartDrawerHTML(data.cart);
          openDrawer();
        } else {
          showToast(data.message || 'Could not add item.', 'error');
        }
      })
      .catch(err => {
        console.error('Cart add error:', err);
        showToast('Error updating bag.', 'error');
      })
      .finally(() => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalText;
        }
      });
    }
  });
}

function refreshCartDrawer() {
  fetch('/bag/drawer-json/', {
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  })
  .then(res => res.json())
  .then(data => {
    if (data.cart) {
      updateCartBadges(data.cart.item_count);
      renderCartDrawerHTML(data.cart);
    }
  })
  .catch(err => console.error('Cart refresh error:', err));
}

function updateCartBadges(count) {
  const badges = document.querySelectorAll('.js-cart-count');
  badges.forEach(b => {
    b.textContent = count;
    b.style.display = count > 0 ? 'flex' : 'none';
  });
}

function renderCartDrawerHTML(cart) {
  const itemsContainer = document.getElementById('cartDrawerItems');
  const subtotalElem = document.getElementById('cartDrawerSubtotal');
  const shippingElem = document.getElementById('cartDrawerShipping');
  const totalElem = document.getElementById('cartDrawerTotal');
  const discountRow = document.getElementById('cartDrawerDiscountRow');
  const discountElem = document.getElementById('cartDrawerDiscount');
  const progressFill = document.getElementById('cartDrawerProgressFill');
  const progressText = document.getElementById('cartDrawerProgressText');

  if (!itemsContainer) return;

  if (cart.items.length === 0) {
    itemsContainer.innerHTML = `
      <div style="text-align:center; padding: 48px 12px; color:#64748b;">
        <div style="font-size:2.8rem; margin-bottom:12px;">🛍️</div>
        <p style="font-family: var(--font-serif); font-size:1.15rem; color:#0f172a; margin-bottom:6px;">Your bag is empty</p>
        <p style="font-size:0.85rem; margin-bottom:20px;">Explore the season's newest arrivals in fashion and clean beauty.</p>
        <a href="/catalog/" class="btn btn-dark btn-sm js-close-cart-drawer">Discover Collections</a>
      </div>
    `;
    if (subtotalElem) subtotalElem.textContent = '₹0.00';
    if (shippingElem) shippingElem.textContent = '₹0.00';
    if (totalElem) totalElem.textContent = '₹0.00';
    if (progressText) progressText.innerHTML = 'Add items to unlock free standard delivery over ₹1,999';
    if (progressFill) progressFill.style.width = '0%';
    return;
  }

  // Render items
  let html = '';
  cart.items.forEach(item => {
    html += `
      <div class="cart-item-card" data-key="${item.key}">
        <img src="${item.product_image}" alt="${item.product_name}" class="cart-item-img">
        <div class="cart-item-info">
          <a href="${item.product_url}" class="cart-item-name">${item.product_name}</a>
          ${item.variant_name ? `<span class="cart-item-variant">${item.variant_type}: <strong>${item.variant_name}</strong></span>` : ''}
          <div class="cart-item-bottom">
            <div class="qty-control">
              <button type="button" class="qty-btn" onclick="updateCartItemQuantity('${item.key}', ${item.quantity - 1})">-</button>
              <span class="qty-num">${item.quantity}</span>
              <button type="button" class="qty-btn" onclick="updateCartItemQuantity('${item.key}', ${item.quantity + 1})">+</button>
            </div>
            <span style="font-weight:700; font-size:0.95rem;">₹${item.total_price}</span>
            <button type="button" class="btn-remove-item" onclick="removeCartItem('${item.key}')">Remove</button>
          </div>
        </div>
      </div>
    `;
  });

  itemsContainer.innerHTML = html;
  if (subtotalElem) subtotalElem.textContent = `₹${cart.subtotal}`;
  if (shippingElem) shippingElem.textContent = cart.is_free_shipping ? 'FREE' : `₹${cart.shipping}`;
  if (totalElem) totalElem.textContent = `₹${cart.grand_total}`;

  if (discountRow && discountElem) {
    if (parseFloat(cart.discount) > 0) {
      discountRow.style.display = 'flex';
      discountElem.textContent = `-₹${cart.discount}`;
    } else {
      discountRow.style.display = 'none';
    }
  }

  if (progressFill && progressText) {
    progressFill.style.width = `${cart.free_shipping_progress}%`;
    if (cart.is_free_shipping) {
      progressText.innerHTML = '✨ You have unlocked <strong>Free Express Shipping!</strong>';
    } else {
      progressText.innerHTML = `Add <strong>₹${cart.free_shipping_remaining}</strong> more for free standard delivery`;
    }
  }
}

function updateCartItemQuantity(key, newQty) {
  const csrfToken = getCookie('csrftoken');
  const formData = new FormData();
  formData.append('key', key);
  formData.append('quantity', newQty);

  fetch('/bag/update/', {
    method: 'POST',
    body: formData,
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': csrfToken,
    }
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === 'success') {
      updateCartBadges(data.cart.item_count);
      renderCartDrawerHTML(data.cart);
    }
  });
}

function removeCartItem(key) {
  const csrfToken = getCookie('csrftoken');
  fetch(`/bag/remove/${encodeURIComponent(key)}/`, {
    method: 'POST',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': csrfToken,
    }
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === 'success') {
      showToast('Item removed from bag', 'info');
      updateCartBadges(data.cart.item_count);
      renderCartDrawerHTML(data.cart);
    }
  });
}

/* ==========================================================================
   Wishlist
   ========================================================================== */
function initWishlist() {
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.js-wishlist-toggle');
    if (!btn) return;
    e.preventDefault();

    const productId = btn.dataset.productId;
    const csrfToken = getCookie('csrftoken');

    fetch(`/account/wishlist/toggle/${productId}/`, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken,
      }
    })
    .then(res => {
      if (res.status === 401) {
        showToast('Please sign in to save items to your wishlist.', 'error');
        setTimeout(() => window.location.href = '/account/login/', 1200);
        throw new Error('Unauthenticated');
      }
      return res.json();
    })
    .then(data => {
      if (data.status === 'success') {
        showToast(data.message, 'success');
        btn.innerHTML = data.is_in_wishlist ? '❤️' : '🤍';
        const badge = document.querySelector('.js-wishlist-count');
        if (badge) {
          badge.textContent = data.count;
          badge.style.display = data.count > 0 ? 'flex' : 'none';
        }
      }
    })
    .catch(err => {
      if (err.message !== 'Unauthenticated') {
        console.error('Wishlist error:', err);
      }
    });
  });
}

/* ==========================================================================
   Generic Modal Manager
   ========================================================================== */
function initModals() {
  const modalBackdrop = document.getElementById('modalBackdrop');
  const closeButtons = document.querySelectorAll('.js-close-modal');

  function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
    if (modalBackdrop) modalBackdrop.classList.remove('active');
    document.body.style.overflow = '';
  }

  closeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal');
      if (modal) closeModal(modal.id);
    });
  });

  if (modalBackdrop) {
    modalBackdrop.addEventListener('click', () => {
      document.querySelectorAll('.modal.active').forEach(m => m.classList.remove('active'));
      modalBackdrop.classList.remove('active');
      document.body.style.overflow = '';
    });
  }
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  const backdrop = document.getElementById('modalBackdrop');
  if (modal) {
    modal.classList.add('active');
    if (backdrop) backdrop.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

/* CSRF Cookie Helper */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
