/**
 * AURA LUXE - Local Media & Visual Similarity Search Engine
 * Interacts with device camera (getUserMedia) and local image uploads,
 * converts photos into visual embeddings, and queries the Python/Pillow matching backend.
 */

let cameraStream = null;

document.addEventListener('DOMContentLoaded', () => {
  initVisualSearchModal();
});

function initVisualSearchModal() {
  const openButtons = document.querySelectorAll('.js-open-visual-search');
  const modal = document.getElementById('visualSearchModal');
  const closeButtons = modal ? modal.querySelectorAll('.js-close-modal') : [];
  const tabCamera = document.getElementById('tabCameraBtn');
  const tabUpload = document.getElementById('tabUploadBtn');
  const viewCamera = document.getElementById('viewCamera');
  const viewUpload = document.getElementById('viewUpload');
  const shutterBtn = document.getElementById('btnShutter');
  const dropzone = document.getElementById('fileDropzone');
  const fileInput = document.getElementById('visualSearchFileInput');
  const form = document.getElementById('visualSearchForm');

  if (!modal) return;

  openButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      openModal('visualSearchModal');
      // Default to opening camera tab if supported
      switchTab('camera');
      startCamera();
    });
  });

  closeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      stopCamera();
    });
  });

  if (tabCamera) {
    tabCamera.addEventListener('click', () => {
      switchTab('camera');
      startCamera();
    });
  }

  if (tabUpload) {
    tabUpload.addEventListener('click', () => {
      switchTab('upload');
      stopCamera();
    });
  }

  function switchTab(tabName) {
    if (tabName === 'camera') {
      if (tabCamera) tabCamera.classList.add('active');
      if (tabUpload) tabUpload.classList.remove('active');
      if (viewCamera) viewCamera.style.display = 'block';
      if (viewUpload) viewUpload.style.display = 'none';
    } else {
      if (tabUpload) tabUpload.classList.add('active');
      if (tabCamera) tabCamera.classList.remove('active');
      if (viewUpload) viewUpload.style.display = 'block';
      if (viewCamera) viewCamera.style.display = 'none';
    }
  }

  // Camera Shutter Snap Action
  if (shutterBtn) {
    shutterBtn.addEventListener('click', () => {
      captureCameraSnapshot();
    });
  }

  // Drag and Drop File Zone
  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    ['dragleave', 'dragend'].forEach(evt => {
      dropzone.addEventListener(evt, () => dropzone.classList.remove('dragover'));
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelection(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files[0]) {
        handleFileSelection(fileInput.files[0]);
      }
    });
  }
}

function startCamera() {
  const videoElem = document.getElementById('cameraStream');
  const cameraError = document.getElementById('cameraError');
  if (!videoElem) return;

  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'environment', // Use back camera if on mobile device
        width: { ideal: 1280 },
        height: { ideal: 720 }
      },
      audio: false
    })
    .then(stream => {
      cameraStream = stream;
      videoElem.srcObject = stream;
      videoElem.play();
      if (cameraError) cameraError.style.display = 'none';
    })
    .catch(err => {
      console.warn('Camera access denied or unavailable:', err);
      if (cameraError) {
        cameraError.style.display = 'block';
        cameraError.innerHTML = '⚠️ Camera access was not permitted. Please upload an image from your device instead.';
      }
    });
  } else {
    if (cameraError) {
      cameraError.style.display = 'block';
      cameraError.innerHTML = 'Media devices not supported in this browser.';
    }
  }
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop());
    cameraStream = null;
  }
}

function captureCameraSnapshot() {
  const videoElem = document.getElementById('cameraStream');
  const canvas = document.getElementById('cameraCanvas') || document.createElement('canvas');
  canvas.id = 'cameraCanvas';
  canvas.style.display = 'none';
  document.body.appendChild(canvas);

  if (!videoElem || !videoElem.videoWidth) {
    showToast('Camera feed is still initializing. Please wait a moment.', 'error');
    return;
  }

  // Set canvas dimensions equal to current video feed
  canvas.width = videoElem.videoWidth;
  canvas.height = videoElem.videoHeight;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(videoElem, 0, 0, canvas.width, canvas.height);

  // Play shutter visual flash
  const flash = document.createElement('div');
  flash.style.position = 'fixed';
  flash.style.top = '0';
  flash.style.left = '0';
  flash.style.width = '100vw';
  flash.style.height = '100vh';
  flash.style.backgroundColor = '#ffffff';
  flash.style.zIndex = '99999';
  flash.style.opacity = '0.85';
  flash.style.transition = 'opacity 0.25s ease';
  document.body.appendChild(flash);
  setTimeout(() => {
    flash.style.opacity = '0';
    setTimeout(() => flash.remove(), 250);
  }, 50);

  // Extract base64 JPEG
  const dataUri = canvas.toDataURL('image/jpeg', 0.85);
  stopCamera();

  // Submit search
  submitVisualSearch({ camera_data: dataUri });
}

function handleFileSelection(file) {
  if (file.size > 10 * 1024 * 1024) {
    showToast('Please select an image smaller than 10MB.', 'error');
    return;
  }

  if (!file.type.startsWith('image/')) {
    showToast('Please select a valid image file (PNG, JPG, WEBP).', 'error');
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    const dataUri = e.target.result;
    submitVisualSearch({ camera_data: dataUri, file: file });
  };
  reader.readAsDataURL(file);
}

function submitVisualSearch(params) {
  const loadingOverlay = document.getElementById('visualSearchLoading');
  if (loadingOverlay) loadingOverlay.style.display = 'flex';

  const form = document.getElementById('visualSearchForm');
  const hiddenDataInput = document.getElementById('hiddenCameraData');

  if (hiddenDataInput && params.camera_data) {
    hiddenDataInput.value = params.camera_data;
  }

  // Standard form submission to visual search results page
  if (form) {
    form.submit();
  }
}
