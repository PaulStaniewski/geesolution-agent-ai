import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeRaw from "rehype-raw";
import rehypeHighlight from "rehype-highlight";

import "./StreamedMarkdown.css";
import "highlight.js/styles/github-dark.min.css";

function normalizeInlineCodeChildren(children) {
    if (typeof children === "string") {
        return children.replace(/^\n+/, "").replace(/\n+$/, "");
    }

    if (Array.isArray(children)) {
        return children
            .map((child) => (typeof child === "string" ? child : ""))
            .join("")
            .replace(/^\n+/, "")
            .replace(/\n+$/, "");
    }

    return "";
}

function isQuizish(text = "") {
    return /(^|\n)\s*a\)/i.test(text) && /(^|\n)\s*b\)/i.test(text);
}

function insertBreakBeforeFirstA(text) {
    return text.replace(/([?.!])\s*(a\))/i, "$1<br>$2");
}

function numberLeadingDots(text) {
    let n = 0;
    return text.replace(/^\s*\.\s+/gm, () => `${++n}. `);
}

function applyQuizFixes(text) {
    if (!isQuizish(text)) return text;

    let result = text;
    result = numberLeadingDots(result);
    result = insertBreakBeforeFirstA(result);

    return result;
}

const markdownComponents = {
    pre({ children }) {
        return <pre className="md-pre">{children}</pre>;
    },

    code({ inline, className, children, ...props }) {
        const classes = [inline ? "md-inline-code" : "md-code-block", className]
            .filter(Boolean)
            .join(" ");

        if (inline) {
            const codeText = normalizeInlineCodeChildren(children);

            return (
                <code className={classes} {...props}>
                    {codeText}
                </code>
            );
        }

        return (
            <code className={classes} {...props}>
                {children}
            </code>
        );
    },
};

const StableMarkdown = React.memo(
    function StableMarkdown({ content, highlight }) {
        return (
            <ReactMarkdown
                components={markdownComponents}
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={
                    highlight
                        ? [rehypeRaw, [rehypeHighlight, { detect: false, ignoreMissing: true }]]
                        : [rehypeRaw]
                }
            >
                {content}
            </ReactMarkdown>
        );
    },
    (prev, next) =>
        prev.content === next.content &&
        prev.highlight === next.highlight
);

export default function StreamedMarkdown({
    text,
    highlight = true,
    transformText,
}) {
    const baseText = text || "";
    const transformedText = transformText ? transformText(baseText) : baseText;
    const preparedText = applyQuizFixes(transformedText);

    return <StableMarkdown content={preparedText} highlight={highlight} />;
}