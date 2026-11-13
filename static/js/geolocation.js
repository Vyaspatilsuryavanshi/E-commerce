/**
 * AURA LUXE - Geolocation & Local Delivery Engine
 * Utilizes HTML5 navigator.geolocation to detect user location,
 * calculate distance to regional luxury boutiques, and auto-fill checkout addresses.
 */

document.addEventListener('DOMContentLoaded', () => {
  initGeolocationTriggers();
  checkCachedLocation();
});

function initGeolocationTriggers() {
  const detectButtons = document.querySelectorAll('.js-detect-location');
  detectButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      requestUserLocation(btn);
    });
  });

  const autofillBtn = document.getElementById('btnAutofillAddressGPS');
  if (autofillBtn) {
    autofillBtn.addEventListener('click', (e) => {
      e.preventDefault();
      requestUserLocationForCheckout(autofillBtn);
    });
  }
}

function checkCachedLocation() {
  const cached = sessionStorage.getItem('aura_user_location');
  if (cached) {
    try {
      const loc = JSON.parse(cached);
      updateHeaderLocationDisplay(loc.city || loc.display);
    } catch (e) {}
  }
}

function requestUserLocation(triggerBtn) {
  if (!('geolocation' in navigator)) {
    showToast('Geolocation is not supported by your browser.', 'error');
    return;
  }

  const originalHtml = triggerBtn ? triggerBtn.innerHTML : '';
  if (triggerBtn) {
    triggerBtn.innerHTML = '<span>📍 Locating...</span>';
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lon = position.coords.longitude;
      
      handleLocationSuccess(lat, lon, triggerBtn, originalHtml);
    },
    (error) => {
      console.warn('Geolocation error:', error);
      let errMsg = 'Location access was denied or timed out.';
      if (error.code === error.PERMISSION_DENIED) {
        errMsg = 'Location permission was denied. You can select your city manually.';
      }
      showToast(errMsg, 'error');
      if (triggerBtn) triggerBtn.innerHTML = originalHtml;
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 60000
    }
  );
}

function handleLocationSuccess(lat, lon, triggerBtn, originalHtml) {
  // Reverse geocode via backend proxy
  fetch(`/checkout/api/reverse-geocode/?lat=${lat}&lon=${lon}`)
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') {
        sessionStorage.setItem('aura_user_location', JSON.stringify(data));
        updateHeaderLocationDisplay(data.city || data.state);
        showToast(`📍 Location set to ${data.city || data.state || 'your current area'}!`, 'success');

        // Fetch nearby stores and update store locator modal if open
        loadNearbyStores(lat, lon);
      }
    })
    .catch(err => {
      console.error('Reverse geocode error:', err);
      showToast('Could not resolve street address from GPS.', 'error');
    })
    .finally(() => {
      if (triggerBtn) triggerBtn.innerHTML = originalHtml;
    });
}

function updateHeaderLocationDisplay(cityName) {
  const headerLocText = document.getElementById('headerLocationText');
  if (headerLocText && cityName) {
    headerLocText.textContent = cityName;
  }
}

function loadNearbyStores(lat, lon) {
  fetch(`/api/nearby-stores/?lat=${lat}&lon=${lon}`)
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') {
        renderNearbyStoresHTML(data);
      }
    })
    .catch(err => console.error('Stores error:', err));
}

function renderNearbyStoresHTML(data) {
  const storeListElem = document.getElementById('nearbyStoresList');
  const deliveryBadge = document.getElementById('locationDeliveryEstimate');

  if (deliveryBadge && data.delivery_estimate) {
    deliveryBadge.textContent = '⚡ ' + String(data.delivery_estimate) + ' delivery available from closest hub.';
  }

  if (!storeListElem) return;
  storeListElem.replaceChildren();

  if (!Array.isArray(data.stores) || data.stores.length === 0) {
    const empty = document.createElement('p');
    empty.className = 'store-empty-state';
    empty.textContent = 'No nearby boutiques are available for this location yet.';
    storeListElem.appendChild(empty);
    return;
  }

  data.stores.forEach((store) => {
    const card = document.createElement('div');
    card.className = 'store-card';
    const details = document.createElement('div');
    const name = document.createElement('div');
    name.className = 'store-name';
    name.textContent = String(store.name ?? 'Boutique');
    const address = document.createElement('div');
    address.style.cssText = 'font-size:0.84rem; color:#64748b; margin-bottom:4px;';
    address.textContent = [store.address, store.city].filter(Boolean).map(String).join(', ');
    const hours = document.createElement('div');
    hours.style.cssText = 'font-size:0.78rem; color:#94a3b8;';
    hours.textContent = String(store.hours ?? '');
    details.append(name, address, hours);

    const meta = document.createElement('div');
    meta.style.textAlign = 'right';
    const distance = document.createElement('span');
    distance.className = 'store-dist-badge';
    distance.textContent = String(store.distance_text ?? '');
    meta.appendChild(distance);
    if (store.express_available) {
      const express = document.createElement('div');
      express.style.cssText = 'font-size:0.75rem; color:#059669; font-weight:600; margin-top:6px;';
      express.textContent = '⚡ Same-Day Courier';
      meta.appendChild(express);
    }
    card.append(details, meta);
    storeListElem.appendChild(card);
  });
}

/* ==========================================================================
   Checkout Page GPS Auto-fill
   ========================================================================== */
function requestUserLocationForCheckout(autofillBtn) {
  if (!('geolocation' in navigator)) {
    showToast('Geolocation is not supported by your device.', 'error');
    return;
  }

  autofillBtn.disabled = true;
  autofillBtn.innerHTML = '<span>📍 Detecting GPS Coordinates...</span>';

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lon = position.coords.longitude;

      fetch(`/checkout/api/reverse-geocode/?lat=${lat}&lon=${lon}`)
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success') {
            // Fill in the form inputs
            const addressInput = document.getElementById('id_address_line_1');
            const cityInput = document.getElementById('id_city');
            const stateInput = document.getElementById('id_state');
            const postalInput = document.getElementById('id_postal_code');
            const countryInput = document.getElementById('id_country');
            const latHidden = document.getElementById('id_shipping_latitude');
            const lonHidden = document.getElementById('id_shipping_longitude');
            const autodetectedHidden = document.getElementById('id_location_autodetected');

            if (addressInput && data.street_address) addressInput.value = data.street_address;
            if (cityInput && data.city) cityInput.value = data.city;
            if (stateInput && data.state) stateInput.value = data.state;
            if (postalInput && data.postal_code) postalInput.value = data.postal_code;
            if (countryInput && data.country) countryInput.value = data.country;
            if (latHidden) latHidden.value = lat;
            if (lonHidden) lonHidden.value = lon;
            if (autodetectedHidden) autodetectedHidden.value = '1';

            showToast('✓ Shipping address auto-filled using your GPS location!', 'success');
          } else {
            showToast('Unable to extract address from coordinates.', 'error');
          }
        })
        .catch(err => {
          console.error(err);
          showToast('Failed to auto-fill address.', 'error');
        })
        .finally(() => {
          autofillBtn.disabled = false;
          autofillBtn.innerHTML = '<span>📍 Re-detect Current Location</span>';
        });
    },
    (err) => {
      console.warn(err);
      showToast('Location access denied. Please type your address.', 'error');
      autofillBtn.disabled = false;
      autofillBtn.innerHTML = '<span>📍 Auto-fill with GPS</span>';
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
}
