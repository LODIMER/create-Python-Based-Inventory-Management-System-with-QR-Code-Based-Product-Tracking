document.addEventListener("DOMContentLoaded", () => {
  const readerEl = document.getElementById("qr-reader");
  const startBtn = document.getElementById("start-camera");
  const stopBtn = document.getElementById("stop-camera");
  const refreshBtn = document.getElementById("refresh-cameras");
  const cameraSelect = document.getElementById("camera-select");
  const statusEl = document.getElementById("scanner-status");
  const form = document.querySelector(".scan-form");
  const tokenInput = form?.querySelector('input[name="token"]');
  const STORAGE_KEY = "stockmark-preferred-camera";

  if (!readerEl || typeof Html5Qrcode === "undefined") {
    return;
  }

  const scanner = new Html5Qrcode("qr-reader");
  let isRunning = false;
  let handled = false;
  let availableCameras = [];

  function setStatus(message, type = "info") {
    if (!statusEl) return;
    statusEl.textContent = message;
    statusEl.dataset.type = type;
  }

  function cameraLabel(camera, index) {
    if (camera.label) {
      return camera.label;
    }
    return `Camera ${index + 1}`;
  }

  function preferredCameraId(cameras) {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && cameras.some((cam) => cam.id === saved)) {
      return saved;
    }

    const rear = cameras.find((cam) =>
      /back|rear|environment/i.test(cam.label || "")
    );
    return rear?.id || cameras[cameras.length - 1]?.id || "";
  }

  function populateCameraSelect(cameras, selectedId) {
    if (!cameraSelect) return;

    cameraSelect.innerHTML = "";

    if (!cameras.length) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "No cameras found";
      cameraSelect.appendChild(option);
      cameraSelect.disabled = true;
      return;
    }

    cameras.forEach((camera, index) => {
      const option = document.createElement("option");
      option.value = camera.id;
      option.textContent = cameraLabel(camera, index);
      cameraSelect.appendChild(option);
    });

    const nextId = selectedId && cameras.some((cam) => cam.id === selectedId)
      ? selectedId
      : preferredCameraId(cameras);

    cameraSelect.value = nextId;
    cameraSelect.disabled = isRunning;
  }

  async function loadCameras(requestPermission = false) {
    if (!cameraSelect) return [];

    cameraSelect.disabled = true;
    setStatus(
      requestPermission
        ? "Requesting camera access to list devices…"
        : "Looking for cameras…",
      "info"
    );

    try {
      if (requestPermission && navigator.mediaDevices?.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        stream.getTracks().forEach((track) => track.stop());
      }

      availableCameras = await Html5Qrcode.getCameras();
      populateCameraSelect(availableCameras, cameraSelect.value || preferredCameraId(availableCameras));

      if (!availableCameras.length) {
        setStatus("No camera found on this device.", "error");
        startBtn.disabled = true;
        return [];
      }

      startBtn.disabled = false;
      if (isRunning) {
        setStatus("Point your camera at a product QR code.", "active");
      } else {
        setStatus("Select a camera and click Start.", "info");
      }
      return availableCameras;
    } catch (err) {
      populateCameraSelect([], "");
      startBtn.disabled = true;
      setStatus(
        err?.message ||
          "Could not access cameras. Check browser permissions and try Refresh list.",
        "error"
      );
      return [];
    }
  }

  function resolveTrackUrl(text) {
    const trimmed = text.trim();
    if (!trimmed) return null;

    try {
      const url = new URL(trimmed, window.location.origin);
      const match = url.pathname.match(/\/track\/([^/]+)\/?$/);
      if (match) {
        return `/track/${match[1]}`;
      }
    } catch (_) {
      /* fall through */
    }

    if (trimmed.includes("/track/")) {
      const token = trimmed.replace(/\/$/, "").split("/track/").pop();
      if (token) {
        return `/track/${token}`;
      }
    }

    return null;
  }

  function handleScanResult(text) {
    if (handled) return;
    handled = true;

    const trackUrl = resolveTrackUrl(text);
    if (trackUrl) {
      setStatus("QR code recognized. Opening product…", "success");
      window.location.href = trackUrl;
      return;
    }

    if (tokenInput && form) {
      tokenInput.value = text.trim();
      setStatus("Code captured. Looking up product…", "success");
      form.submit();
    }
  }

  async function stopScanner(updateStatus = true) {
    if (!isRunning) {
      if (cameraSelect) {
        cameraSelect.disabled = false;
      }
      return;
    }

    try {
      await scanner.stop();
      await scanner.clear();
    } catch (_) {
      /* ignore stop errors */
    }

    isRunning = false;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    if (cameraSelect) {
      cameraSelect.disabled = false;
    }
    if (updateStatus) {
      setStatus("Camera stopped.", "info");
    }
  }

  async function startScanner() {
    if (isRunning) return;

    const cameraId = cameraSelect?.value;
    if (!cameraId) {
      setStatus("Select a camera before starting.", "error");
      return;
    }

    handled = false;
    startBtn.disabled = true;
    stopBtn.disabled = false;
    if (cameraSelect) {
      cameraSelect.disabled = true;
    }
    setStatus("Starting selected camera…", "info");

    try {
      await scanner.start(
        cameraId,
        {
          fps: 10,
          qrbox: { width: 250, height: 250 },
          aspectRatio: 1,
        },
        (decodedText) => {
          stopScanner(false).then(() => handleScanResult(decodedText));
        },
        () => {
          /* ignore scan failures while searching */
        }
      );

      isRunning = true;
      localStorage.setItem(STORAGE_KEY, cameraId);
      setStatus("Point your camera at a product QR code.", "active");

      await loadCameras(false);
      if (cameraSelect) {
        cameraSelect.value = cameraId;
        cameraSelect.disabled = true;
      }
    } catch (err) {
      isRunning = false;
      startBtn.disabled = false;
      stopBtn.disabled = true;
      if (cameraSelect) {
        cameraSelect.disabled = false;
      }
      setStatus(
        err?.message ||
          "Could not start the selected camera. Try another device or refresh the list.",
        "error"
      );
    }
  }

  async function switchCamera() {
    if (!isRunning || !cameraSelect?.value) return;

    const nextCameraId = cameraSelect.value;
    setStatus("Switching camera…", "info");
    await stopScanner(false);
    await startScanner();
    if (cameraSelect) {
      cameraSelect.value = nextCameraId;
    }
  }

  startBtn?.addEventListener("click", startScanner);
  stopBtn?.addEventListener("click", () => stopScanner(true));
  refreshBtn?.addEventListener("click", () => loadCameras(true));

  cameraSelect?.addEventListener("change", () => {
    localStorage.setItem(STORAGE_KEY, cameraSelect.value);
    if (isRunning) {
      switchCamera();
    }
  });

  loadCameras(false);

  window.addEventListener("beforeunload", () => {
    if (isRunning) {
      scanner.stop().catch(() => {});
    }
  });
});
