function waitForEvent(target, eventName, errorName = 'error') {
  return new Promise((resolve, reject) => {
    const cleanup = () => {
      target.removeEventListener(eventName, onSuccess);
      target.removeEventListener(errorName, onError);
    };
    const onSuccess = () => {
      cleanup();
      resolve();
    };
    const onError = () => {
      cleanup();
      reject(new Error('Could not load media from that URL.'));
    };
    target.addEventListener(eventName, onSuccess, { once: true });
    target.addEventListener(errorName, onError, { once: true });
  });
}

function seekVideo(video, seconds) {
  return new Promise((resolve, reject) => {
    const cleanup = () => {
      video.removeEventListener('seeked', onSeeked);
      video.removeEventListener('error', onError);
    };
    const onSeeked = () => {
      cleanup();
      resolve();
    };
    const onError = () => {
      cleanup();
      reject(new Error('Could not decode frames from that clip.'));
    };
    video.addEventListener('seeked', onSeeked, { once: true });
    video.addEventListener('error', onError, { once: true });
    video.currentTime = seconds;
  });
}

function canvasToBlob(canvas, type = 'image/png', quality) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        reject(new Error('Could not capture a frame from that clip.'));
        return;
      }
      resolve(blob);
    }, type, quality);
  });
}

function formatTime(seconds) {
  const whole = Math.max(0, Math.round(seconds));
  const mins = Math.floor(whole / 60);
  const secs = whole % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

export async function extractFramesFromClipUrl(url, { frameCount = 3, maxDurationSeconds = 45 } = {}) {
  const video = document.createElement('video');
  video.crossOrigin = 'anonymous';
  video.preload = 'auto';
  video.muted = true;
  video.playsInline = true;
  video.src = url;

  await waitForEvent(video, 'loadedmetadata');

  if (!Number.isFinite(video.duration) || video.duration <= 0) {
    throw new Error('That clip did not expose a usable duration.');
  }
  if (video.duration > maxDurationSeconds) {
    throw new Error(`Only short clips up to ${maxDurationSeconds} seconds are supported right now.`);
  }

  if (video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
    await waitForEvent(video, 'loadeddata');
  }

  const width = video.videoWidth;
  const height = video.videoHeight;
  if (!width || !height) {
    throw new Error('That clip did not expose a usable frame size.');
  }

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  if (!ctx) {
    throw new Error('Could not start frame extraction in this browser.');
  }

  const frames = [];
  const usableFrameCount = Math.max(1, frameCount);
  for (let index = 0; index < usableFrameCount; index += 1) {
    const seconds = ((index + 1) / (usableFrameCount + 1)) * video.duration;
    await seekVideo(video, seconds);
    try {
      ctx.drawImage(video, 0, 0, width, height);
    } catch {
      throw new Error(
        'This clip blocks canvas extraction. Try a direct MP4/WebM/MOV link that allows public frame access.',
      );
    }
    const blob = await canvasToBlob(canvas, 'image/png');
    const file = new File([blob], `clip-frame-${index + 1}.png`, { type: 'image/png' });
    frames.push({
      file,
      previewUrl: URL.createObjectURL(blob),
      seconds,
      label: formatTime(seconds),
    });
  }

  video.removeAttribute('src');
  video.load();

  return {
    durationSeconds: video.duration,
    frameCount: frames.length,
    frames,
  };
}
