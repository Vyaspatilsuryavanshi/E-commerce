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
  drawer.addEventListener('click', (event) => {
    const actionButton = event.target.closest('[data-cart-action]');
    if (!actionButton) return;
    const card = actionButton.closest('.cart-item-card');
    const key = card?.dataset.key;
    if (!key) return;
    const quantity = Number(card.querySelector('.qty-num')?.textContent || 0);
    if (actionButton.dataset.cartAction === 'increase') updateCartItemQuantity(key, quantity + 1);
    else if (actionButton.dataset.cartAction === 'decrease') updateCartItemQuantity(key, quantity - 1);
    else if (actionButton.dataset.cartAction === 'remove') removeCartItem(key);
    else if (actionButton.dataset.cartAction === 'close') closeDrawer();
  });

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

  if (!itemsContainer || !cart || !Array.isArray(cart.items)) return;
  itemsContainer.replaceChildren();

  if (cart.items.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'cart-empty-state';
    const icon = document.createElement('div');
    icon.className = 'cart-empty-icon';
    icon.textContent = '🛍️';
    const title = document.createElement('p');
    title.className = 'cart-empty-title';
    title.textContent = 'Your bag is empty';
    const description = document.createElement('p');
    description.className = 'cart-empty-description';
    description.textContent = "Explore the season's newest arrivals in fashion and clean beauty.";
    const link = document.createElement('a');
    link.href = '/catalog/';
    link.className = 'btn btn-dark btn-sm';
    link.textContent = 'Discover Collections';
    empty.append(icon, title, description, link);
    itemsContainer.appendChild(empty);
    if (subtotalElem) subtotalElem.textContent = '₹0.00';
    if (shippingElem) shippingElem.textContent = '₹0.00';
    if (totalElem) totalElem.textContent = '₹0.00';
    if (progressText) progressText.textContent = 'Add items to unlock free standard delivery over ₹1,999';
    if (progressFill) progressFill.style.width = '0%';
    if (discountRow) discountRow.style.display = 'none';
    return;
  }

  cart.items.forEach((item) => {
    const card = document.createElement('div');
    card.className = 'cart-item-card';
    card.dataset.key = String(item.key ?? '');

    const image = document.createElement('img');
    image.className = 'cart-item-img';
    image.alt = String(item.product_name ?? 'Product');
    image.loading = 'lazy';
    const imageUrl = String(item.product_image ?? '');
    if (imageUrl.startsWith('/') || imageUrl.startsWith('https://')) image.src = imageUrl;

    const info = document.createElement('div');
    info.className = 'cart-item-info';
    const name = document.createElement('a');
    name.className = 'cart-item-name';
    const productUrl = String(item.product_url ?? '');
    name.href = productUrl.startsWith('/') ? productUrl : '/catalog/';
    name.textContent = String(item.product_name ?? 'Product');
    info.appendChild(name);

    if (item.variant_name) {
      const variant = document.createElement('span');
      variant.className = 'cart-item-variant';
      variant.textContent = String(item.variant_type ?? 'Option') + ': ' + String(item.variant_name);
      info.appendChild(variant);
    }

    const bottom = document.createElement('div');
    bottom.className = 'cart-item-bottom';
    const controls = document.createElement('div');
    controls.className = 'qty-control';

    const decrease = document.createElement('button');
    decrease.type = 'button';
    decrease.className = 'qty-btn';
    decrease.dataset.cartAction = 'decrease';
    decrease.setAttribute('aria-label', 'Decrease quantity of ' + name.textContent);
    decrease.textContent = '−';

    const quantity = document.createElement('span');
    quantity.className = 'qty-num';
    quantity.textContent = String(Number(item.quantity) || 0);

    const increase = document.createElement('button');
    increase.type = 'button';
    increase.className = 'qty-btn';
    increase.dataset.cartAction = 'increase';
    increase.setAttribute('aria-label', 'Increase quantity of ' + name.textContent);
    increase.textContent = '+';

    controls.append(decrease, quantity, increase);

    const price = document.createElement('span');
    price.style.cssText = 'font-weight:700; font-size:0.95rem;';
    price.textContent = '₹' + String(item.total_price ?? '0.00');

    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'btn-remove-item';
    remove.dataset.cartAction = 'remove';
    remove.textContent = 'Remove';

    bottom.append(controls, price, remove);
    info.appendChild(bottom);
    card.append(image, info);
    itemsContainer.appendChild(card);
  });

  if (subtotalElem) subtotalElem.textContent = '₹' + String(cart.subtotal ?? '0.00');
  if (shippingElem) shippingElem.textContent = cart.is_free_shipping ? 'FREE' : '₹' + String(cart.shipping ?? '0.00');
  if (totalElem) totalElem.textContent = '₹' + String(cart.grand_total ?? '0.00');

  if (discountRow && discountElem) {
    if (Number(cart.discount) > 0) {
      discountRow.style.display = 'flex';
      discountElem.textContent = '-₹' + String(cart.discount);
    } else {
      discountRow.style.display = 'none';
    }
  }

  if (progressFill && progressText) {
    const progress = Math.min(100, Math.max(0, Number(cart.free_shipping_progress) || 0));
    progressFill.style.width = progress + '%';
    progressText.textContent = cart.is_free_shipping
      ? '✨ You have unlocked Free Express Shipping!'
      : 'Add ₹' + String(cart.free_shipping_remaining ?? '0.00') + ' more for free standard delivery';
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
