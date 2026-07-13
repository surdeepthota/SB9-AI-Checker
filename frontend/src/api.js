// All URLs are relative: the Vite dev server proxies them to FastAPI (see
// vite.config.js), and in production FastAPI serves the built frontend itself.

async function toJsonOrThrow(response) {
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body.detail) detail = String(body.detail);
    } catch { /* keep the generic message */ }
    throw new Error(detail);
  }
  return response.json();
}

export async function analyzeFile(file, isCampaignAd) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('is_campaign_ad', isCampaignAd ? 'true' : 'false');
  return toJsonOrThrow(await fetch('/analyze', { method: 'POST', body: formData }));
}

export async function analyzeSample(filename, isCampaignAd) {
  return toJsonOrThrow(
    await fetch('/analyze-sample', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename, is_campaign_ad: isCampaignAd }),
    }),
  );
}

export async function listSamples() {
  return toJsonOrThrow(await fetch('/samples'));
}

export async function buildPacket(trustReport, exemptionAnswers, publisher) {
  return toJsonOrThrow(
    await fetch('/packet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        trust_report: trustReport,
        exemption_answers: exemptionAnswers,
        publisher: publisher || null,
      }),
    }),
  );
}
