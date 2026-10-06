/**
 * Dashboard shell. The panels below are placeholders mapping 1:1 to the
 * planned features — implement them under src/components/ and src/pages/
 * and wire them to the backend through src/api/client.ts.
 */
export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>RAT — Repo Analysis Tool</h1>
        <p>Repository metrics per author, file, directory and commit set</p>
      </header>

      <main className="app-main">
        {/* TODO: FilterBar — repository, author, path, time range, commit list */}
        <section className="panel">
          <h2>Filters</h2>
          <p className="placeholder">
            Repository / author / file-or-directory / commit selection goes here.
          </p>
        </section>

        {/* TODO: ingestion — zip upload + clone URL forms */}
        <section className="panel">
          <h2>Add Repository</h2>
          <p className="placeholder">Zip upload and clone-by-URL forms go here.</p>
        </section>

        {/* TODO: metric panels per category */}
        <section className="panel">
          <h2>Metrics</h2>
          <p className="placeholder">
            File / Directory / Repository / Commit Set metric panels go here.
          </p>
        </section>

        {/* TODO: author merging UI (.mailmap applied automatically, manual merges here) */}
        <section className="panel">
          <h2>Authors</h2>
          <p className="placeholder">Author list and manual merging go here.</p>
        </section>
      </main>
    </div>
  );
}
