### Prompt to implement the new “Lease (Simple)” tab

Implement a new simplified tab that lets users upload a JSON and a DOCX, automatically derives the key-value mapping from the JSON, and runs the replacement. Keep the existing “Lease Population” tab unchanged. In the new tab, exclude Manual Entry, CSV/Excel, and Paste Table. For Exhibit A, assume parcels are not portions.

- Create a new tab “Lease (Simple)” next to the existing `Lease Population` tab in `templates/index.html`.
- The new tab should:
  - Show two inputs: JSON file and DOCX file.
  - Parse JSON into key-value mapping (same logic and UI preview as the existing JSON section).
  - On “Start Replacement”, POST to `/lease_population_replace` with:
    - `docx`: the selected DOCX file.
    - `mapping`: JSON.stringify([...key-value pairs...]) derived from the uploaded JSON.
    - `track_changes`: false by default.
    - `document_name`: optional, derived from JSON (fallback: `lease_population_filled`).
  - Download the returned DOCX result automatically on success.
- Important: Scope all new querySelectors and event handlers to the new tab’s container so removing buttons from the existing “Lease Population” tab never causes null references. Do not attach listeners to missing elements. Always check for element existence before adding listeners in shared code.
- Do not modify or remove the current “Lease Population” tab’s functionality.
- Do not rely on the `/parse_kv_table` route or any manual/paste table code from the old tab.

Edits

1) File: `templates/index.html`
- Add a nav link for a new tab, e.g.:
```html
<a href="#" class="nav-link" data-tab="lease-population-simple">Lease (Simple)</a>
```
- Add a new content container after the existing lease tab:
```html
<div class="tab-content" id="lease-population-simple-tab">
  <div class="main-content">
    <h1>Lease Population (Simple)</h1>

    <!-- JSON Upload -->
    <div id="simpleJsonSection" style="margin-bottom:2rem;">
      <h3>Upload JSON Mapping</h3>
      <div style="border:2px dashed #00bfff; border-radius:8px; padding:1.25rem;">
        <input type="file" id="simpleJsonInput" accept=".json" style="display:none;">
        <button type="button" class="submit-btn" id="simpleBrowseJsonBtn">Browse JSON</button>
      </div>
      <div id="simpleJsonInfo" style="display:none; margin-top:0.5rem;">
        <strong>Selected:</strong> <span id="simpleJsonName"></span> <span id="simpleJsonSize" style="margin-left:0.5rem;"></span>
      </div>
      <div style="margin-top:0.75rem;">
        <button type="button" class="submit-btn" id="simpleParseJsonBtn" disabled>Parse JSON</button>
        <button type="button" class="secondary-btn" id="simpleClearJsonBtn" disabled>Clear</button>
      </div>
      <div id="simpleJsonParseStatus" style="display:none; margin-top:0.5rem;"></div>
      <div id="simpleJsonPreviewSection" style="display:none; margin-top:1rem;">
        <h4>Parsed Key-Value Preview</h4>
        <div style="max-height:260px; overflow:auto; border:1px solid #00bfff; border-radius:6px;">
          <table class="preview-table" id="simpleJsonPreviewTable">
            <thead><tr><th>Key</th><th>Value</th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- DOCX Upload -->
    <div id="simpleDocxSection" style="margin-bottom:2rem;">
      <h3>Upload DOCX</h3>
      <input type="file" id="simpleDocxInput" accept=".docx">
      <div id="simpleDocxInfo" style="display:none; margin-top:0.5rem;">
        <strong>Selected:</strong> <span id="simpleDocxName"></span> <span id="simpleDocxSize" style="margin-left:0.5rem;"></span>
      </div>
    </div>

    <!-- Exhibit A (Simple) -->
    <div id="simpleExhibitSection" style="margin-bottom:2rem;">
      <h3>Generate Exhibit A (Simple)</h3>
      <p style="color:#b5e0ff;">Assume parcels are not portions. Enter parcel descriptions only.</p>
      <div style="margin-bottom:0.5rem;">
        <label># of Parcels</label>
        <input type="number" id="simpleNumParcels" min="0" value="0" style="width:6rem;">
        <button type="button" class="secondary-btn" id="simpleBuildParcelsBtn">Build Fields</button>
      </div>
      <div id="simpleParcelsContainer" style="display:grid; gap:0.5rem;"></div>
      <div style="margin-top:0.75rem;">
        <button type="button" class="secondary-btn" id="simpleGenerateExhibitBtn">Generate Exhibit A</button>
      </div>
      <div id="simpleExhibitStatus" style="display:none; margin-top:0.5rem;"></div>
    </div>

    <!-- Submit -->
    <div style="margin-top:1rem;">
      <button type="button" class="submit-btn" id="simpleStartBtn" disabled>Start Replacement</button>
      <div id="simpleSubmitStatus" style="display:none; margin-top:0.75rem;"></div>
    </div>
  </div>
</div>
```

- In the existing inline script, add a new initializer that runs on DOMContentLoaded and only touches elements within `#lease-population-simple-tab`. Reuse the JSON parsing logic from the existing tab, but scoped to the “simple” IDs. Do not reference any removed buttons.

Example script additions (IDs must match the HTML above):
```html
<script>
document.addEventListener('DOMContentLoaded', () => {
  const simpleTab = document.getElementById('lease-population-simple-tab');
  if (!simpleTab) return;

  // Nav linking already works via existing logic (data-tab switching)

  // Elements
  const simpleJsonInput = simpleTab.querySelector('#simpleJsonInput');
  const simpleBrowseJsonBtn = simpleTab.querySelector('#simpleBrowseJsonBtn');
  const simpleJsonInfo = simpleTab.querySelector('#simpleJsonInfo');
  const simpleJsonName = simpleTab.querySelector('#simpleJsonName');
  const simpleJsonSize = simpleTab.querySelector('#simpleJsonSize');
  const simpleParseJsonBtn = simpleTab.querySelector('#simpleParseJsonBtn');
  const simpleClearJsonBtn = simpleTab.querySelector('#simpleClearJsonBtn');
  const simpleJsonParseStatus = simpleTab.querySelector('#simpleJsonParseStatus');
  const simpleJsonPreviewSection = simpleTab.querySelector('#simpleJsonPreviewSection');
  const simpleJsonPreviewTable = simpleTab.querySelector('#simpleJsonPreviewTable tbody');

  const simpleDocxInput = simpleTab.querySelector('#simpleDocxInput');
  const simpleDocxInfo = simpleTab.querySelector('#simpleDocxInfo');
  const simpleDocxName = simpleTab.querySelector('#simpleDocxName');
  const simpleDocxSize = simpleTab.querySelector('#simpleDocxSize');

  const simpleStartBtn = simpleTab.querySelector('#simpleStartBtn');
  const simpleSubmitStatus = simpleTab.querySelector('#simpleSubmitStatus');

  const simpleNumParcels = simpleTab.querySelector('#simpleNumParcels');
  const simpleBuildParcelsBtn = simpleTab.querySelector('#simpleBuildParcelsBtn');
  const simpleParcelsContainer = simpleTab.querySelector('#simpleParcelsContainer');
  const simpleGenerateExhibitBtn = simpleTab.querySelector('#simpleGenerateExhibitBtn');
  const simpleExhibitStatus = simpleTab.querySelector('#simpleExhibitStatus');

  let parsedJsonMapping = [];
  let currentJsonData = null;

  // JSON browse
  simpleBrowseJsonBtn.onclick = () => simpleJsonInput.click();

  simpleJsonInput.onchange = () => {
    const file = simpleJsonInput.files[0];
    if (file) {
      simpleJsonName.textContent = file.name;
      simpleJsonSize.textContent = `(${(file.size/1024).toFixed(1)} KB)`;
      simpleJsonInfo.style.display = 'block';
      simpleParseJsonBtn.disabled = false;
      simpleClearJsonBtn.disabled = false;
      simpleJsonParseStatus.style.display = 'none';
      simpleJsonPreviewSection.style.display = 'none';
      updateStartEnabled();
    }
  };

  simpleClearJsonBtn.onclick = () => {
    simpleJsonInput.value = '';
    simpleJsonInfo.style.display = 'none';
    simpleParseJsonBtn.disabled = true;
    simpleClearJsonBtn.disabled = true;
    simpleJsonParseStatus.style.display = 'none';
    simpleJsonPreviewSection.style.display = 'none';
    currentJsonData = null;
    parsedJsonMapping = [];
    simpleJsonPreviewTable.innerHTML = '';
    updateStartEnabled();
  };

  simpleParseJsonBtn.onclick = async () => {
    const file = simpleJsonInput.files[0];
    if (!file) return;
    try {
      simpleJsonParseStatus.style.display = 'block';
      simpleJsonParseStatus.innerHTML = '<div style="color:#00bfff;">Parsing JSON...</div>';
      const text = await file.text();
      const jsonData = JSON.parse(text);
      parsedJsonMapping = [];
      if (Array.isArray(jsonData)) {
        parsedJsonMapping = jsonData.filter(item => item.key && item.value);
      } else if (typeof jsonData === 'object' && jsonData) {
        parsedJsonMapping = Object.entries(jsonData).map(([k, v]) => ({ key: String(k), value: String(v) }));
      }
      if (parsedJsonMapping.length === 0) throw new Error('No valid key-value pairs found');
      simpleJsonPreviewTable.innerHTML = '';
      parsedJsonMapping.forEach(({key, value}) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${key}</td><td>${value}</td>`;
        simpleJsonPreviewTable.appendChild(tr);
      });
      simpleJsonParseStatus.innerHTML = `<div style="color:#00ff7f;">Parsed ${parsedJsonMapping.length} pairs</div>`;
      simpleJsonPreviewSection.style.display = 'block';
    } catch (err) {
      console.error(err);
      simpleJsonParseStatus.innerHTML = `<div style="color:#ff6b6b;">Error: ${err.message}</div>`;
      simpleJsonPreviewSection.style.display = 'none';
    } finally {
      updateStartEnabled();
    }
  };

  // DOCX
  simpleDocxInput.onchange = () => {
    const f = simpleDocxInput.files[0];
    if (f) {
      simpleDocxInfo.style.display = 'block';
      simpleDocxName.textContent = f.name;
      simpleDocxSize.textContent = `(${(f.size/1024).toFixed(1)} KB)`;
    } else {
      simpleDocxInfo.style.display = 'none';
    }
    updateStartEnabled();
  };

  function updateStartEnabled() {
    simpleStartBtn.disabled = !(parsedJsonMapping.length > 0 && simpleDocxInput.files && simpleDocxInput.files[0]);
  }

  // Exhibit A (Simple: no portions)
  simpleBuildParcelsBtn.onclick = () => {
    const n = parseInt(simpleNumParcels.value || '0', 10) || 0;
    simpleParcelsContainer.innerHTML = '';
    for (let i=1; i<=n; i++) {
      const div = document.createElement('div');
      div.innerHTML = `
        <label>Parcel ${i} Description</label>
        <textarea class="simple-parcel" placeholder="Enter full parcel description"></textarea>
      `;
      simpleParcelsContainer.appendChild(div);
    }
  };

  simpleGenerateExhibitBtn.onclick = () => {
    const parcels = Array.from(simpleParcelsContainer.querySelectorAll('.simple-parcel')).map(t => t.value.trim()).filter(Boolean);
    if (parcels.length === 0) {
      simpleExhibitStatus.style.display = 'block';
      simpleExhibitStatus.innerHTML = '<div style="color:#ff6b6b;">Please add at least one parcel description.</div>';
      return;
    }
    const header = 'EXHIBIT A';
    const body = parcels.map((p, idx) => `Parcel ${idx+1}:\n${p}`).join('\n\n');
    const exhibitString = `${header}\n\n${body}`;
    // Inject into mapping under a known key; adjust if your templates use a different placeholder
    const keyName = '[EXHIBIT A]';
    const idxExisting = parsedJsonMapping.findIndex(p => p.key.trim().toLowerCase() === keyName.toLowerCase());
    if (idxExisting >= 0) parsedJsonMapping[idxExisting].value = exhibitString;
    else parsedJsonMapping.push({ key: keyName, value: exhibitString });

    simpleExhibitStatus.style.display = 'block';
    simpleExhibitStatus.innerHTML = '<div style="color:#00ff7f;">Added Exhibit A to mapping.</div>';
    updateStartEnabled();
  };

  // Submit to backend
  simpleStartBtn.onclick = async () => {
    if (parsedJsonMapping.length === 0 || !simpleDocxInput.files[0]) return;
    simpleSubmitStatus.style.display = 'block';
    simpleSubmitStatus.innerHTML = '<div style="color:#00bfff;">Submitting...</div>';
    const form = new FormData();
    form.append('docx', simpleDocxInput.files[0]);
    form.append('mapping', JSON.stringify(parsedJsonMapping));
    form.append('track_changes', 'false');
    // Optional: derive a name if present in mapping or JSON
    const nameKV = parsedJsonMapping.find(p => p.key.trim().toLowerCase() === 'document_name');
    if (nameKV && nameKV.value) form.append('document_name', nameKV.value);

    try {
      const res = await fetch('/lease_population_replace', { method: 'POST', body: form });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || `Request failed (${res.status})`);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'lease_population_filled.docx';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      simpleSubmitStatus.innerHTML = '<div style="color:#00ff7f;">Success! Download started.</div>';
    } catch (err) {
      simpleSubmitStatus.innerHTML = `<div style=\"color:#ff6b6b;\">Error: ${err.message}</div>`;
    }
  };
});
</script>
```

- Ensure none of the above code references elements from the old tab. All selectors must be scoped via `simpleTab.querySelector(...)`. Do not add listeners to non-existent IDs.

2) Backend
- No backend changes are required. The new tab should call the existing `/lease_population_replace` route with the `docx` and `mapping` form fields as described.

Acceptance criteria
- A new “Lease (Simple)” tab exists, switchable via the top nav.
- The simple tab accepts JSON + DOCX only.
- JSON is parsed into key-value pairs and previewed.
- Clicking “Start Replacement” posts to `/lease_population_replace` and downloads the returned DOCX.
- Exhibit A generation in the simple tab only supports non-portion parcels and injects the combined text into the mapping under `[EXHIBIT A]` (adjust if your templates use a different placeholder).
- Removing Manual/CSV/Paste buttons from the old tab does not break any JavaScript: no console errors due to missing elements.

Notes
- Keep all new event listeners guarded by element existence and scoped to `#lease-population-simple-tab`.
- Preserve the project’s current indentation/formatting style in `templates/index.html`.

- If your template expects a different placeholder for Exhibit A, replace `[EXHIBIT A]` accordingly.

- To test locally:
  - Start server on port 5001.
  - Go to the “Lease (Simple)” tab.
  - Upload a JSON (object or array of {key,value}) and a DOCX; click “Start Replacement.”
  - Verify the download and applied changes.

- Do not remove or modify existing advanced features in the original tab.

- Do not reference or attach handlers to `manualInputBtn`, `uploadTableBtn`, or `pasteTableBtn` anywhere in the simplified flow.

- If any shared functions must be reused, copy them and rename with the “simple” prefix to keep the new tab decoupled.

- If an image embedding key is present (e.g., `[EXHIBIT_A_IMAGE_1]`), leave it untouched; the simple tab only generates Exhibit A text without portions.

- Ensure the new tab does not alter existing behavior of `/lease_population_replace`.

- Keep the DOCX field name as `docx` and the mapping field as `mapping` to match the backend.

- Use `track_changes=false` by default.

- On success, infer a sensible filename or just use `lease_population_filled.docx` for the download.

- No changes to routes are required; do not add new endpoints.

- No global JS errors when old buttons are removed from the main tab.

- Keep code self-contained and minimal.

- Ship with working UI and successful end-to-end replacement.

- Include brief comments only where necessary; avoid excessive inline explanations.

- Validate that the app builds and the new tab works.

- Commit changes on branch `lean_mvp_2`.


- Implement the new “Lease (Simple)” tab in `templates/index.html` with scoped JS and no references to removed elements.
- Ensure it posts JSON mapping + DOCX to `/lease_population_replace` and downloads the result.
- Simple Exhibit A: parcels only, no portions; inject text to mapping.


