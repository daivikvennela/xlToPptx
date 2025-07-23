class DynamicSlideEditor {
  constructor(template) { this.template = template; }

  async load() {
    // Fetch the mapping JSON for the selected template
    const map = await fetch(`/api/template_v2/${encodeURIComponent(this.template)}`)
      .then(r => r.json());
    this.map = map;
    this.renderForm(map.textboxes || []);
    this.showPreservationNotice();
  }

  renderForm(textboxes) {
    const container = document.getElementById('editor');
    container.innerHTML = '';
    if (!textboxes.length) {
      container.innerHTML = '<div style="color:#b91c1c;">No editable textboxes found in this template.</div>';
      return;
    }
    textboxes.forEach(tb => {
      const wrapper = document.createElement('div');
      wrapper.style.marginBottom = '1.5em';
      const label = document.createElement('label');
      label.htmlFor = `tb_${tb.shape_id}`;
      label.innerText = tb.role || tb.name;
      const field = document.createElement('textarea');
      field.id = `tb_${tb.shape_id}`;
      field.maxLength = tb.styles && tb.styles.max_chars ? tb.styles.max_chars : 500;
      field.value = tb.text_preview || '';
      wrapper.appendChild(label);
      wrapper.appendChild(field);
      container.appendChild(wrapper);
    });
  }

  showPreservationNotice() {
    alert("All backgrounds, layouts, fonts, colors, and masters remain 100% intact. You may only edit text.");
  }

  async save() {
    const updates = (this.map.textboxes || []).map(tb => ({
      shape_id: tb.shape_id,
      new_text: document.getElementById(`tb_${tb.shape_id}`).value
    }));
    const blob = await fetch('/api/render_slide_v2', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template: this.template, updates })
    }).then(r => r.blob());
    this.downloadBlob(blob, `${this.template}_custom.pptx`);
  }

  downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }
} 