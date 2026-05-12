import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzePlant } from '../api/scans';

function readAsDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = e => resolve(e.target.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export default function ScanPlant() {
  const navigate   = useNavigate();
  const inputRef   = useRef(null);

  const [file,     setFile]     = useState(null);
  const [city,     setCity]     = useState('Skopje');
  const [preview,  setPreview]  = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState('');

  const acceptFile = useCallback(async (f) => {
    if (!f || !f.type.startsWith('image/')) {
      setError('Please select a valid image file (JPG, PNG, or WEBP).');
      return;
    }
    if (f.size > 5 * 1024 * 1024) {
      setError('Image exceeds the 5 MB limit. Please choose a smaller file.');
      return;
    }
    setError('');
    setFile(f);
    setPreview(await readAsDataURL(f));
  }, []);

  function handleInputChange(e) {
    acceptFile(e.target.files[0]);
  }

  function handleDragOver(e) {
    e.preventDefault();
    setDragOver(true);
  }

  function handleDragLeave() {
    setDragOver(false);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    acceptFile(e.dataTransfer.files[0]);
  }

  async function handleAnalyze() {
    if (!file || loading) return;
    setError('');
    setLoading(true);
    try {
      const result = await analyzePlant(file, city);
      navigate('/results', { state: { result } });
    } catch (err) {
      const msg = err.response?.data?.error
        ?? err.response?.data?.detail
        ?? 'Analysis failed. Please try again.';
      setError(msg);
      setLoading(false);
    }
  }

  const uploadZoneClass = `upload-zone glass-card${dragOver ? ' dragover' : ''}`;

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Scan <span>Plant</span></div>
        <div className="page-sub">Upload a plant photo for AI-powered disease analysis</div>
      </div>

      <div className="scan-layout">
        {/* ── Left: upload zone ── */}
        <div>
          <div
            className={uploadZoneClass}
            onClick={() => !loading && inputRef.current.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            style={{ cursor: loading ? 'default' : 'pointer' }}
          >
            <span className="upload-icon">
              {file ? '✅' : '🌿'}
            </span>
            <div className="upload-title">
              {file ? file.name : 'Drop your plant photo here'}
            </div>
            <div className="upload-sub">
              {file
                ? `${(file.size / 1024 / 1024).toFixed(1)} MB · ready to analyse`
                : <>Supports JPG, PNG, WEBP · Max 5 MB<br />For best results, photograph in natural daylight</>
              }
            </div>
            <div className="upload-btn-area">
              <button
                className="btn btn-primary"
                disabled={loading}
                onClick={e => { e.stopPropagation(); inputRef.current.click(); }}
              >
                📁 Browse Files
              </button>
            </div>
          </div>

          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={handleInputChange}
          />

          <div className="scan-field glass-card">
            <label htmlFor="scan-city">City for weather context</label>
            <input
              id="scan-city"
              type="text"
              value={city}
              onChange={e => setCity(e.target.value)}
              placeholder="Skopje"
              disabled={loading}
            />
          </div>

          {error && (
            <div style={{
              marginTop: 12,
              padding: '10px 14px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--error-dim)',
              border: '1px solid var(--error-border)',
              color: 'var(--error)',
              fontSize: 12,
              lineHeight: 1.5,
            }}>
              {error}
            </div>
          )}
        </div>

        {/* ── Right: preview + analyse ── */}
        <div>
          <div className="section-label" style={{ marginBottom: 10 }}>Image Preview</div>

          <div className="preview-box glass-card" style={{ height: 220, position: 'relative' }}>
            {preview ? (
              <>
                <img src={preview} alt="Plant preview" style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
                {loading && (
                  <div style={{
                    position: 'absolute', inset: 0,
                    background: 'rgba(10,26,14,0.75)',
                    display: 'flex', flexDirection: 'column',
                    alignItems: 'center', justifyContent: 'center',
                    gap: 12,
                  }}>
                    <Spinner />
                    <span style={{ fontSize: 13, color: 'var(--accent)', fontWeight: 600 }}>
                      Analysing…
                    </span>
                  </div>
                )}
              </>
            ) : (
              <span>No image selected</span>
            )}
          </div>

          <div className="analyze-btn-wrap">
            <button
              className="btn btn-primary"
              style={{
                width: '100%',
                justifyContent: 'center',
                padding: 13,
                opacity: (!file || loading) ? 0.55 : 1,
                cursor: (!file || loading) ? 'default' : 'pointer',
              }}
              disabled={!file || loading}
              onClick={handleAnalyze}
            >
              {loading ? '⏳ Analysing…' : '🔬 Analyse Plant'}
            </button>
          </div>

          <div style={{ marginTop: 10 }}>
            <div className="glass-card" style={{ padding: 14 }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.8 }}>
                <div style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 6, fontSize: 12 }}>
                  📷 Good photo tips
                </div>
                <div>✓ Fill frame with affected area</div>
                <div>✓ Use natural daylight</div>
                <div>✓ Avoid blurry or dark shots</div>
                <div>✓ Include both sides of leaf</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <div style={{
      width: 28, height: 28,
      border: '3px solid rgba(61,220,110,0.2)',
      borderTopColor: 'var(--accent)',
      borderRadius: '50%',
      animation: 'spin 0.75s linear infinite',
    }} />
  );
}
