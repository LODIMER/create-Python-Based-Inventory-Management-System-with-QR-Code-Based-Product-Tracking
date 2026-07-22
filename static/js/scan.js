document.addEventListener("DOMContentLoaded", () => {
  const readerEl = document.getElementById("qr-reader");
  const startBtn = document.getElementById("start-camera");
  const stopBtn = document.getElementById("stop-camera");
  const statusEl = document.getElementById("scanner-status");
  const form = document.querySelector(".scan-form");
  const tokenInput = form?.querySelector('input[name="token"]');

  if (!readerEl || typeof Html5Qrcode === "undefined") {
    return;
  }
  
  const scanner = new Html5Qrcode("qr-reader");
  let isRunning = false;
  let handled = false;

  function setStatus(message, type = "info") {
    if (!statusEl) return;
    statusEl.textContent = message;
    statusEl.dataset.type = type;
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

  async function stopScanner() {
    if (!isRunning) return;

    try {
      await scanner.stop();
      await scanner.clear();
    } catch (_) {
      /* ignore stop errors */
    }

    isRunning = false;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    setStatus("Camera stopped.", "info");
  }

  async function startScanner() {
    if (isRunning) return;

    handled = false;
    startBtn.disabled = true;
    stopBtn.disabled = false;
    setStatus("Requesting camera access…", "info");

    try {
      const cameras = await Html5Qrcode.getCameras();
      if (!cameras.length) {
        throw new Error("No camera found on this device.");
      }

      const preferred =
        cameras.find((cam) => /back|rear|environment/i.test(cam.label)) ||
        cameras[cameras.length - 1];

      await scanner.start(
        preferred.id,
        {
          fps: 10,
          qrbox: { width: 250, height: 250 },
          aspectRatio: 1,
        },
        (decodedText) => {
          stopScanner().then(() => handleScanResult(decodedText));
        },
        () => {
          /* ignore scan failures while searching */
        }
      );

      isRunning = true;
      setStatus("Point your camera at a product QR code.", "active");
    } catch (err) {
      startBtn.disabled = false;
      stopBtn.disabled = true;
      setStatus(
        err?.message ||
          "Could not start the camera. Check browser permissions and try again.",
        "error"
      );
    }
  }

  startBtn?.addEventListener("click", startScanner);
  stopBtn?.addEventListener("click", stopScanner);

  window.addEventListener("beforeunload", () => {
    if (isRunning) {
      scanner.stop().catch(() => {});
    }
  });
});
