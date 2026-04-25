import "./SourcesList.css";

const normalizeNumber = (value) => {
    const n = Number(value);
    return Number.isFinite(n) ? n : undefined;
};

const buildKey = (hit) => {
    const url = hit?.url || "";
    const anchor = hit?.anchor || "";

    if (url) {
        return `${url}#${anchor}`;
    }

    const file = hit?.file_name || "";
    const id = hit?.doc_id || "";
    return `${file}|${id}`;
};

const buildHref = (hit) => {
    if (!hit?.url) return null;

    // Doc anchors are already slugs, so they should not be encoded again.
    return hit.anchor ? `${hit.url}#${hit.anchor}` : hit.url;
};

const buildLabel = (hit) => {
    const base = hit?.title || "Source";
    const idx = normalizeNumber(hit?.chunk_index);

    if (hit?.anchor) return `${base} §${hit.anchor}`;
    if (idx !== undefined) return `${base} #${idx}`;
    return base;
};

const dedupeAndSort = (hits = []) => {
    const best = new Map();

    for (const hit of hits) {
        const key = buildKey(hit);
        const score = normalizeNumber(hit?.score) ?? -Infinity;
        const previous = best.get(key);

        if (!previous || (normalizeNumber(previous.score) ?? -Infinity) < score) {
            best.set(key, { ...hit, score });
        }
    }

    return Array.from(best.values()).sort(
        (a, b) =>
            (normalizeNumber(b.score) ?? -Infinity) -
            (normalizeNumber(a.score) ?? -Infinity)
    );
};

const SourcesList = ({ hits = [], limit = 5 }) => {
    const webHits = Array.isArray(hits) ? hits.filter((hit) => Boolean(hit?.url)) : [];
    const items = dedupeAndSort(webHits).slice(0, limit);

    if (!items.length) return null;

    return (
        <div className="sources">
            <div className="sources-title">Sources</div>

            <ul className="sources-list">
                {items.map((hit) => {
                    const href = buildHref(hit);
                    const label = buildLabel(hit);
                    const score = normalizeNumber(hit?.score);

                    return (
                        <li key={buildKey(hit)} className="sources-item">
                            {href ? (
                                <a
                                    href={href}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="sources-link"
                                >
                                    {label}
                                </a>
                            ) : (
                                <span className="sources-text">{label}</span>
                            )}

                            {score !== undefined && (
                                <span className="sources-score">
                                    ({score.toFixed(3)})
                                </span>
                            )}
                        </li>
                    );
                })}
            </ul>
        </div>
    );
};

export default SourcesList;