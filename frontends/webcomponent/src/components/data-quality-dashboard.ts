import { LitElement, css, html } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import './plotly-chart.js';

interface CleaningAction {
  action: string;
  column?: string;
}

interface QualityReport {
  summary: {
    row_count: number;
    column_count: number;
    duplicate_row_count: number;
    missing_cell_count: number;
  };
  scores: {
    overall: number;
    completeness: number;
    uniqueness: number;
    validity: number;
    consistency: number;
  };
  columns: Array<{
    name: string;
    data_type: string;
    missing_count: number;
    unique_count: number;
    outlier_count: number;
    mean?: number;
    median?: number;
  }>;
  issues: string[];
}

interface Recommendation {
  action: string;
  column?: string;
  affected_records: number;
  affected_percentage: number;
  reason: string;
  risks: string;
  expected_impact: string;
}

interface DatasetMetadata {
  dataset_id: string;
  original_filename: string | null;
  file_type: string;
  row_count: number | null;
  column_count: number | null;
  created_at: string | null;
  source?: string;
}

interface ChartColumn {
  name: string;
  data_type: string;
  numeric: boolean;
}

interface ChartResult {
  columns: ChartColumn[];
  traces: Array<Record<string, unknown>>;
  summary: { rows: number; value_column: string };
}

@customElement('data-quality-dashboard')
export class DataQualityDashboard extends LitElement {
  static styles = css`
    :host {
      --space-1: 4px;
      --space-2: 8px;
      --space-3: 12px;
      --space-4: 16px;
      --space-5: 24px;
      --border: #d5e5e5;
      --navy: #023d60;
      --teal: #15a8a8;
      display: block;
      width: 100%;
      max-width: 1180px;
      margin: 16px auto;
      color: #183c4d;
    }
    .panel {
      min-width: 0;
      padding: var(--space-4);
      border: 1px solid var(--border);
      border-radius: 14px;
      background: #fff;
      overflow: hidden;
    }
    .toolbar, .score-grid, .actions { display: flex; gap: var(--space-3); flex-wrap: wrap; align-items: center; }
    section > nav.toolbar { gap: var(--space-3); padding-bottom: var(--space-3); border-bottom: 1px solid #e4eeee; }
    section > .toolbar { padding: var(--space-3); border: 1px solid #e4eeee; border-radius: 10px; background: #fbfefe; }
    .score-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: var(--space-3); margin: var(--space-4) 0; }
    .score { min-width: 0; min-height: 72px; padding: 12px; border-radius: 10px; background: #edfafa; color: var(--navy); }
    .score span { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12px; }
    .score strong { display: block; margin-top: 6px; font-size: 20px; line-height: 1; }
    button, select, input { min-width: 0; height: 36px; padding: 0 10px; border: 1px solid #b8d5d5; border-radius: 8px; font: inherit; }
    button { cursor: pointer; background: var(--teal); color: white; border: 0; font-size: 13px; font-weight: 600; white-space: nowrap; }
    button.secondary { background: #023d60; }
    button:hover { filter: brightness(.96); }
    table { width: 100%; margin-top: var(--space-3); border-collapse: collapse; font-size: 13px; }
    th, td { height: 36px; padding: 8px 10px; border-bottom: 1px solid #e4eeee; text-align: left; }
    .muted { color: #5d7180; font-size: 13px; }
    .error { color: #a33a27; }
    .success { color: #087f83; }
    .section { margin-top: var(--space-4); padding-top: var(--space-4); border-top: 1px solid #e4eeee; }
    .upload-row { display: flex; gap: var(--space-3); min-height: 36px; align-items: center; flex-wrap: wrap; }
    .upload-row input[type="file"] { max-width: 100%; }
    .dataset-list { display: grid; gap: 4px; margin-top: 10px; max-height: 260px; overflow: auto; }
    .dataset-item { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 12px; align-items: center; padding: 7px 9px; border-bottom: 1px solid #e4eeee; }
    .dataset-item small { display: block; }
    .preview { overflow: auto; max-height: 260px; }
    .nav-button { min-width: 96px; border-radius: 999px; padding: 0 14px; font-size: 12px; }
    .nav-button.active { background: #15a8a8; }
    .analytics-grid { display: grid; grid-template-columns: minmax(260px, .75fr) minmax(0, 1.25fr); gap: var(--space-4); align-items: stretch; }
    .chart-controls { display: grid; gap: var(--space-3); align-content: start; }
    .chart-controls label { display: grid; gap: 5px; color: #355565; font-size: 12px; font-weight: 600; }
    .chart-controls select, .chart-controls input { width: 100%; }
    .chart-preview { min-width: 0; min-height: 420px; padding: var(--space-4); border: 1px solid var(--border); border-radius: 12px; background: #fbfefe; overflow: hidden; }
    .chart-preview h4 { margin: 0 0 var(--space-2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .chart-preview plotly-chart { display: block; width: 100%; height: 340px; }
    .chart-actions { display: flex; gap: var(--space-2); flex-wrap: wrap; }
    @media (max-width: 760px) {
      .analytics-grid { grid-template-columns: 1fr; }
      .chart-preview { min-height: 360px; }
      .chart-preview plotly-chart { height: 300px; }
    }
    @media (max-width: 700px) {
      .score-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .dataset-item { grid-template-columns: 1fr; }
      .toolbar > input, .toolbar > select { flex: 1 1 160px; }
      table { min-width: 620px; }
    }
  `;

  @property({ attribute: 'api-base' }) apiBaseUrl = '';
  @property() initialDataset = 'Customer';
  @state() private datasetId = this.initialDataset;
  @state() private versionId = this.initialDataset;
  @state() private report?: QualityReport;
  @state() private recommendations: Recommendation[] = [];
  @state() private selected = new Set<number>();
  @state() private preview?: Record<string, any>;
  @state() private versions: Array<Record<string, any>> = [];
  @state() private history: Array<Record<string, any>> = [];
  @state() private datasets: DatasetMetadata[] = [];
  @state() private previewRows: Record<string, unknown>[] = [];
  @state() private previewColumns: string[] = [];
  @state() private uploadName = '';
  @state() private uploadError = '';
  @state() private uploadLoading = false;
  @state() private status = '';
  @state() private error = '';
  @state() private loading = false;
  @state() private activeSection = 'overview';
  @state() private chartType = 'bar';
  @state() private chartX = '';
  @state() private chartY = '';
  @state() private chartGroup = '';
  @state() private chartAggregation = 'sum';
  @state() private chartSort = 'default';
  @state() private chartTitle = 'Dataset visualization';
  @state() private chartLimit = 25;
  @state() private chartResult?: ChartResult;
  @state() private chartLoading = false;
  @state() private chartError = '';

  connectedCallback(): void {
    super.connectedCallback();
    void this.loadDatasets();
    void this.loadDataset();
  }

  private endpoint(path: string): string {
    return `${this.apiBaseUrl}${path}`;
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(this.endpoint(path), {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed with HTTP ${response.status}`);
    }
    return response.json() as Promise<T>;
  }

  private async loadDatasets(): Promise<void> {
    try {
      const response = await this.request<{ datasets: DatasetMetadata[] }>('/api/data-quality/datasets');
      this.datasets = response.datasets;
    } catch (error) {
      this.uploadError = error instanceof Error ? error.message : 'Unable to load datasets';
    }
  }

  private async uploadDataset(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const allowed = ['.csv', '.json', '.xlsx'];
    const extension = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    this.uploadName = file.name;
    this.uploadError = '';
    if (!allowed.includes(extension)) {
      this.uploadError = 'Choose a CSV, JSON, or XLSX file.';
      input.value = '';
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      this.uploadError = 'The file must be smaller than 10 MiB.';
      input.value = '';
      return;
    }
    this.uploadLoading = true;
    try {
      const body = new FormData();
      body.append('file', file);
      const response = await fetch(this.endpoint('/api/data-quality/datasets/upload'), {
        method: 'POST',
        body,
        credentials: 'same-origin',
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || `Upload failed with HTTP ${response.status}`);
      this.datasetId = result.dataset_id;
      this.versionId = result.dataset_id;
      this.status = `Uploaded ${file.name} as ${result.dataset_id}`;
      await this.loadDatasets();
      await this.loadDataset();
    } catch (error) {
      this.uploadError = error instanceof Error ? error.message : 'Dataset upload failed';
    } finally {
      this.uploadLoading = false;
      input.value = '';
    }
  }

  private openUploadPicker(): void {
    this.shadowRoot?.querySelector<HTMLInputElement>('#dataset-upload')?.click();
  }

  private scrollToSection(sectionId: string): void {
    this.activeSection = sectionId;
  }

  private async previewDataset(): Promise<void> {
    try {
      const result = await this.request<{
        rows: Record<string, unknown>[];
        columns: Array<{ name: string }>;
      }>('/api/data-quality/datasets/preview', {
        method: 'POST',
        body: JSON.stringify({ dataset_id: this.datasetId, limit: 20 }),
      });
      this.previewRows = result.rows;
      this.previewColumns = result.columns.map(column => column.name);
      this.status = `Preview loaded for ${this.datasetId}`;
    } catch (error) {
      this.error = error instanceof Error ? error.message : 'Unable to preview dataset';
    }
  }

  private async loadDataset(): Promise<void> {
    this.error = '';
    this.loading = true;
    this.preview = undefined;
    this.selected = new Set<number>();
    try {
      this.report = await this.request<QualityReport>(
        `/api/data-quality/profile/${encodeURIComponent(this.datasetId)}`,
      );
      const numericColumn = this.report.columns.find(column => ['int64', 'float64', 'int32', 'float32'].includes(column.data_type));
      const categoryColumn = this.report.columns.find(column => !['int64', 'float64', 'int32', 'float32'].includes(column.data_type));
      this.chartX = categoryColumn?.name || this.report.columns[0]?.name || '';
      this.chartY = numericColumn?.name || this.report.columns[0]?.name || '';
      this.chartGroup = '';
      this.chartResult = undefined;
      const response = await this.request<{ recommendations: Recommendation[] }>(
        '/api/data-quality/recommendations',
        { method: 'POST', body: JSON.stringify({ dataset_id: this.datasetId }) },
      );
      this.recommendations = response.recommendations;
      const versionResponse = await this.request<{ versions: Array<Record<string, any>> }>(
        `/api/data-quality/versions/${encodeURIComponent(this.datasetId)}`,
      );
      this.versions = versionResponse.versions;
      const historyResponse = await this.request<{ history: Array<Record<string, any>> }>(
        `/api/data-quality/history/${encodeURIComponent(this.datasetId)}`,
      );
      this.history = historyResponse.history;
      const availableVersionIds = this.versions.map(version => version.version_id);
      const selectedVersion = availableVersionIds.includes(this.versionId)
        ? this.versionId
        : this.datasetId;
      this.selectVersion(selectedVersion);
      this.status = `Profiled ${this.datasetId}`;
    } catch (error) {
      this.error = error instanceof Error ? error.message : 'Unable to load dataset';
    } finally {
      this.loading = false;
    }
  }

  private changeDataset(event: Event): void {
    this.datasetId = (event.target as HTMLInputElement).value.trim();
    this.versionId = this.datasetId;
    void this.loadDataset();
  }

  private selectVersion(versionId: string): void {
    this.versionId = versionId;
    window.dispatchEvent(new CustomEvent('dataset-version-changed', {
      detail: { datasetId: this.datasetId, versionId },
    }));
    this.chartResult = undefined;
  }

  private async generateChart(): Promise<void> {
    this.chartLoading = true;
    this.chartError = '';
    try {
      this.chartResult = await this.request<ChartResult>('/api/data-quality/chart-data', {
        method: 'POST',
        body: JSON.stringify({
          dataset_id: this.datasetId,
          version_id: this.versionId,
          chart_type: this.chartType,
          x_column: this.chartX,
          y_column: this.chartY || undefined,
          group_by: this.chartGroup || undefined,
          aggregation: this.chartAggregation,
          sort_order: this.chartSort,
          limit: this.chartLimit,
        }),
      });
      this.chartTitle = `${this.chartType.replace('-', ' ')} of ${this.chartY || 'records'} by ${this.chartX}`;
    } catch (error) {
      this.chartError = error instanceof Error ? error.message : 'Unable to generate chart';
    } finally {
      this.chartLoading = false;
    }
  }

  private resetChart(): void {
    this.chartType = 'bar';
    this.chartAggregation = 'sum';
    this.chartSort = 'default';
    this.chartLimit = 25;
    this.chartResult = undefined;
    this.chartError = '';
  }

  private toggleRecommendation(index: number): void {
    const selected = new Set(this.selected);
    if (selected.has(index)) selected.delete(index);
    else selected.add(index);
    this.selected = selected;
  }

  private selectedActions(): CleaningAction[] {
    return [...this.selected].map((index) => {
      const recommendation = this.recommendations[index];
      return { action: recommendation.action, ...(recommendation.column ? { column: recommendation.column } : {}) };
    });
  }

  private async previewCleaning(): Promise<void> {
    try {
      this.preview = await this.request<Record<string, any>>('/api/data-quality/clean/preview', {
        method: 'POST',
        body: JSON.stringify({ dataset_id: this.datasetId, actions: this.selectedActions() }),
      });
      this.status = 'Preview ready; the original table was not changed.';
    } catch (error) {
      this.error = error instanceof Error ? error.message : 'Unable to preview cleaning';
    }
  }

  private async executeCleaning(): Promise<void> {
    if (!this.preview || !window.confirm('Create a cleaned dataset version?')) return;
    try {
      const result = await this.request<{ version_id: string }>('/api/data-quality/clean/execute', {
        method: 'POST',
        body: JSON.stringify({
          dataset_id: this.datasetId,
          actions: this.selectedActions(),
          approved: true,
        }),
      });
      this.versionId = result.version_id;
      this.status = `Created cleaned version ${result.version_id}`;
      await this.loadDataset();
      this.selectVersion(result.version_id);
    } catch (error) {
      this.error = error instanceof Error ? error.message : 'Unable to execute cleaning';
    }
  }

  private async rollback(versionId: string): Promise<void> {
      if (!window.confirm(`Create a rollback version from ${versionId}?`)) return;
      try {
        const result = await this.request<{ version_id: string }>('/api/data-quality/rollback', {
          method: 'POST',
          body: JSON.stringify({ dataset_id: this.datasetId, version_id: versionId }),
        });
        this.status = `Created rollback version ${result.version_id}`;
        await this.loadDataset();
        this.selectVersion(result.version_id);
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Unable to rollback version';
      }
  }

  render() {
    return html`
      <section class="panel" aria-label="Data quality dashboard">
        <nav class="toolbar" aria-label="Data quality navigation">
          ${[
            ['overview', 'Overview'],
            ['datasets', 'Datasets'],
            ['profiling', 'Data Profiling'],
            ['cleaning', 'Data Cleaning'],
            ['versions', 'Version History'],
            ['analytics', 'AI Analytics'],
          ].map(([sectionId, label]) => html`
            <button class="secondary nav-button ${this.activeSection === sectionId ? 'active' : ''}" @click=${() => this.scrollToSection(sectionId)}>${label}</button>
          `)}
        </nav>
        <div ?hidden=${this.activeSection !== 'datasets'} id="datasets" class="section" style="margin-top: 0; padding-top: 0; border-top: 0;">
          <h2>Dataset Management</h2>
          <div class="upload-row">
            <button @click=${this.openUploadPicker} ?disabled=${this.uploadLoading}>Upload Dataset</button>
            <input id="dataset-upload" hidden type="file" accept=".csv,.json,.xlsx,text/csv,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" @change=${this.uploadDataset} ?disabled=${this.uploadLoading}>
            ${this.uploadLoading ? html`<span role="status">Uploading...</span>` : ''}
            ${this.uploadName && !this.uploadLoading ? html`<span class="muted">${this.uploadName}</span>` : ''}
          </div>
          ${this.uploadError ? html`<p class="error" role="alert">${this.uploadError}</p>` : ''}
          <div class="dataset-list" aria-label="Available datasets">
            ${this.datasets.map(dataset => html`
              <div class="dataset-item">
                <span><strong>${dataset.original_filename || dataset.dataset_id}</strong>
                  <small class="muted">(${dataset.dataset_id}) · ${dataset.row_count ?? '—'} rows · ${dataset.column_count ?? '—'} columns</small>
                </span>
                <button class="secondary" @click=${() => { this.datasetId = dataset.dataset_id; this.versionId = dataset.dataset_id; void this.loadDataset(); }}>Select</button>
              </div>
            `)}
          </div>
        </div>
        <div ?hidden=${this.activeSection !== 'overview'} id="overview" class="section" style="margin-top: 0; padding-top: 0; border-top: 0;">
          <div class="toolbar">
            <strong>Selected dataset</strong>
            <span class="muted">${this.datasetId}</span>
            <button @click=${this.openUploadPicker}>Upload Dataset</button>
            <button class="secondary" @click=${() => this.activeSection = 'datasets'}>Manage datasets</button>
          </div>
        </div>
        <div class="toolbar">
          <strong>Data Quality</strong>
          <input .value=${this.datasetId} @change=${this.changeDataset} aria-label="Dataset table">
          <select .value=${this.versionId} ?disabled=${this.loading} @change=${(event: Event) => this.selectVersion((event.target as HTMLSelectElement).value)} aria-label="Dataset version">
            ${this.versions.map(version => html`<option value=${version.version_id}>${version.is_original ? 'Original' : `Cleaned v${version.version_number}`}</option>`)}
          </select>
          <button class="secondary" ?disabled=${this.loading} @click=${() => this.loadDataset()}>${this.loading ? 'Loading...' : 'Refresh profile'}</button>
          <button @click=${this.previewDataset} ?disabled=${this.loading}>Preview dataset</button>
        </div>
        ${this.error ? html`<p class="error" role="alert">${this.error}</p>` : ''}
        ${this.status ? html`<p class="muted" role="status">${this.status}</p>` : ''}
        ${this.previewRows.length ? html`
          <div ?hidden=${this.activeSection !== 'overview'} id="preview" class="section preview" aria-label="Dataset preview">
            <h2>Data Preview</h2>
            <table><thead><tr>${this.previewColumns.map(column => html`<th>${column}</th>`)}</tr></thead>
              <tbody>${this.previewRows.map(row => html`<tr>${this.previewColumns.map(column => html`<td>${row[column] ?? ''}</td>`)}</tr>`)}</tbody>
            </table>
          </div>
        ` : ''}
        ${this.report ? html`
          <div ?hidden=${this.activeSection !== 'overview'} class="score-grid">
            ${Object.entries(this.report.scores).map(([name, value]) => html`<div class="score"><span>${name}</span><strong>${value}</strong></div>`)}
          </div>
          <p class="muted">${this.report.summary.row_count} rows, ${this.report.summary.column_count} columns,
            ${this.report.summary.missing_cell_count} missing cells, ${this.report.summary.duplicate_row_count} duplicate rows.</p>
          <div ?hidden=${this.activeSection !== 'profiling'} id="profiling">
          <table>
            <thead><tr><th>Column</th><th>Type</th><th>Missing</th><th>Unique</th><th>Outliers</th><th>Median</th></tr></thead>
            <tbody>${this.report.columns.map(column => html`
              <tr><td>${column.name}</td><td>${column.data_type}</td><td>${column.missing_count}</td>
              <td>${column.unique_count}</td><td>${column.outlier_count}</td><td>${column.median ?? '-'}</td></tr>
            `)}</tbody>
          </table>
          </div>
          <div ?hidden=${this.activeSection !== 'cleaning'} id="cleaning">
          <h3>Cleaning recommendations</h3>
          ${this.recommendations.map((recommendation, index) => html`
            <label class="muted"><input type="checkbox" .checked=${this.selected.has(index)} @change=${() => this.toggleRecommendation(index)}>
              ${recommendation.action} ${recommendation.column ? `(${recommendation.column})` : ''} —
              ${recommendation.affected_records} records (${recommendation.affected_percentage}%)
            </label><br>
          `)}
          <div class="actions">
            <button @click=${this.previewCleaning} ?disabled=${this.selected.size === 0}>Preview cleaning</button>
            ${this.preview ? html`<button class="secondary" @click=${this.executeCleaning}>Approve and create version</button>` : ''}
          </div>
          ${this.preview ? html`<p class="muted">Preview: ${this.preview.preview.after_rows} rows after cleaning,
            ${this.preview.preview.changed_cells} changed cells. Quality: ${this.preview.quality_before.scores.overall}
            → ${this.preview.quality_after.scores.overall}.</p>` : ''}
          </div>
          <div ?hidden=${this.activeSection !== 'versions'} id="versions">
          <h3>Cleaning history</h3>
          <table>
            <thead><tr><th>Version</th><th>Created</th><th>Operations</th><th>Quality</th><th></th></tr></thead>
            <tbody>${this.history.map(item => html`
              <tr>
                <td>${item.version_table}</td><td>${item.created_at}</td>
                <td>${item.actions.map((action: CleaningAction) => action.action).join(', ')}</td>
                <td>${item.quality_before.scores.overall} → ${item.quality_after.scores.overall}</td>
                <td><button @click=${() => this.rollback(item.version_table)}>Rollback</button></td>
              </tr>
            `)}</tbody>
          </table>
          </div>
          <div ?hidden=${this.activeSection !== 'analytics'} id="analytics" class="section">
            <h3>AI Analytics</h3>
            <p class="muted">Build an interactive visualization from the selected dataset version.</p>
            ${this.report ? html`
              ${(() => {
                const columns: ChartColumn[] = this.report!.columns.map(column => ({
                  name: column.name,
                  data_type: column.data_type,
                  numeric: ['int64', 'float64', 'int32', 'float32'].includes(column.data_type),
                }));
                return html`
                  <div class="analytics-grid">
                    <div class="panel chart-controls">
                      <label>Chart type
                        <select .value=${this.chartType} @change=${(event: Event) => this.chartType = (event.target as HTMLSelectElement).value}>
                          <option value="bar">Bar Chart</option>
                          <option value="horizontal-bar">Horizontal Bar Chart</option>
                          <option value="line">Line Chart</option>
                          <option value="area">Area Chart</option>
                          <option value="pie">Pie Chart</option>
                          <option value="donut">Donut Chart</option>
                          <option value="scatter">Scatter Plot</option>
                          <option value="histogram">Histogram</option>
                          <option value="box">Box Plot</option>
                          <option value="heatmap">Heatmap</option>
                        </select>
                      </label>
                      <label>X-axis
                        <select .value=${this.chartX} @change=${(event: Event) => this.chartX = (event.target as HTMLSelectElement).value}>
                          ${columns.map(column => html`<option value=${column.name}>${column.name} (${column.data_type})</option>`)}
                        </select>
                      </label>
                      <label>Y-axis
                        <select .value=${this.chartY} @change=${(event: Event) => this.chartY = (event.target as HTMLSelectElement).value}>
                          <option value="">Count records</option>
                          ${columns.filter(column => column.numeric).map(column => html`<option value=${column.name}>${column.name} (${column.data_type})</option>`)}
                        </select>
                      </label>
                      <label>Group by
                        <select .value=${this.chartGroup} @change=${(event: Event) => this.chartGroup = (event.target as HTMLSelectElement).value}>
                          <option value="">No grouping</option>
                          ${columns.filter(column => !column.numeric).map(column => html`<option value=${column.name}>${column.name}</option>`)}
                        </select>
                      </label>
                      <label>Aggregation
                        <select .value=${this.chartAggregation} @change=${(event: Event) => this.chartAggregation = (event.target as HTMLSelectElement).value}>
                          <option value="sum">Sum</option><option value="average">Average</option>
                          <option value="count">Count</option><option value="minimum">Minimum</option>
                          <option value="maximum">Maximum</option><option value="median">Median</option>
                        </select>
                      </label>
                      <label>Sort order
                        <select .value=${this.chartSort} @change=${(event: Event) => this.chartSort = (event.target as HTMLSelectElement).value}>
                          <option value="default">Default</option><option value="ascending">Ascending</option><option value="descending">Descending</option>
                        </select>
                      </label>
                      <label>Chart title
                        <input .value=${this.chartTitle} @input=${(event: Event) => this.chartTitle = (event.target as HTMLInputElement).value}>
                      </label>
                      <label>Limit
                        <input type="number" min="1" max="200" .value=${String(this.chartLimit)} @input=${(event: Event) => this.chartLimit = Number((event.target as HTMLInputElement).value) || 25}>
                      </label>
                      <div class="chart-actions">
                        <button @click=${this.generateChart} ?disabled=${this.chartLoading || !this.chartX}>${this.chartLoading ? 'Generating...' : 'Generate Chart'}</button>
                        <button class="secondary" @click=${this.resetChart}>Reset</button>
                      </div>
                    </div>
                    <div class="chart-preview">
                      ${this.chartError ? html`<p class="error" role="alert">${this.chartError}</p>` : ''}
                      ${this.chartResult ? html`
                        <h4>${this.chartTitle}</h4>
                        <plotly-chart
                          .data=${this.chartResult.traces}
                          .layout=${{
                            title: this.chartTitle,
                            xaxis: { title: this.chartX },
                            yaxis: { title: this.chartY || 'Records' },
                            showlegend: Boolean(this.chartGroup),
                            height: 390,
                            margin: { t: 48, r: 18, b: 72, l: 64 },
                          }}
                          theme="light">
                        </plotly-chart>
                        <p class="muted">${this.chartResult.summary.rows} plotted rows using ${this.chartResult.summary.value_column}.</p>
                      ` : html`<p class="muted">Choose columns and generate a chart using actual data.</p>`}
                    </div>
                  </div>
                `;
              })()}
            ` : html`<p class="muted">Load a dataset before creating a visualization.</p>`}
          </div>
        ` : html`<p class="muted">Choose a table to generate its quality profile.</p>`}
      </section>
    `;
  }
}
