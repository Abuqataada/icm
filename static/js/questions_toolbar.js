// static/js/questions_toolbar.js
// Math toolbar for question + option textareas
(function () {
    // ====== helpers ======
    const supMap = {"0":"⁰","1":"¹","2":"²","3":"³","4":"⁴","5":"⁵","6":"⁶","7":"⁷","8":"⁸","9":"⁹"};
    const subMap = {"0":"₀","1":"₁","2":"₂","3":"₃","4":"₄","5":"₅","6":"₆","7":"₇","8":"₈","9":"₉"};

    function toSuperscript(s) {
        return String(s).split('').map(c => supMap[c] || c).join('');
    }
    function toSubscript(s) {
        return String(s).split('').map(c => subMap[c] || c).join('');
    }

    function insertAtCursor(textarea, insertText, cursorInsideOffset = null) {
        if (!textarea) return;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const before = textarea.value.slice(0, start);
        const after = textarea.value.slice(end);
        textarea.value = before + insertText + after;

        // If cursorInsideOffset provided, place cursor relative to start (number)
        if (Number.isInteger(cursorInsideOffset)) {
            const pos = start + cursorInsideOffset;
            textarea.setSelectionRange(pos, pos);
        } else {
            const pos = start + insertText.length;
            textarea.setSelectionRange(pos, pos);
        }
        textarea.focus();
        updateCharCountFor(textarea);
    }

    function updateCharCountFor(textarea) {
        const ccId = textarea.dataset.charcount;
        const max = parseInt(textarea.dataset.maxlength) || 1000;
        if (!ccId) return;
        const el = document.getElementById(ccId);
        if (!el) return;
        const len = textarea.value.length;
        el.textContent = `${len}/${max} characters`;
        if (len > Math.floor(max * 0.9)) el.classList.add('text-danger'); else el.classList.remove('text-danger');
    }

    function handleAction(action, textarea) {
        if (!textarea) return;
        switch (action) {
            case 'power': {
                const v = prompt("Enter the exponent (digits or text). Example: 2 → x² :");
                if (v === null) return;
                insertAtCursor(textarea, toSuperscript(v));
                break;
            }
            case 'subscript': {
                const v = prompt("Enter the subscript (digits or text). Example: 2 → x₂ :");
                if (v === null) return;
                insertAtCursor(textarea, toSubscript(v));
                break;
            }
            case 'root': {
                const v = prompt("Enter root index (e.g., 2 for √(), 3 for ³√() ) :");
                if (v === null) return;
                const idx = Number(v);
                if (isNaN(idx) || idx < 2) {
                    alert("Please enter a valid integer ≥ 2");
                    return;
                }
                if (idx === 2) {
                    // insert √() and place cursor inside parentheses
                    insertAtCursor(textarea, '√()', 2);
                } else {
                    const sup = toSuperscript(v);
                    // insert like ³√() and place cursor inside parentheses
                    const inserted = `${sup}√()`;
                    const insideOffset = sup.length + 2; // after sup + '√('
                    insertAtCursor(textarea, inserted, insideOffset);
                }
                break;
            }
            case 'fraction': {
                const v = prompt("Enter fraction as numerator/denominator (e.g., 1/2):");
                if (v === null) return;
                const parts = v.split('/');
                if (parts.length !== 2) {
                    alert("Please use format: numerator/denominator");
                    return;
                }
                const num = toSuperscript(parts[0].trim());
                const den = toSubscript(parts[1].trim());
                insertAtCursor(textarea, `${num}⁄${den}`);
                break;
            }
            // simple symbol insertions
            case 'pi': insertAtCursor(textarea, 'π'); break;
            case 'theta': insertAtCursor(textarea, 'θ'); break;
            case 'sigma': insertAtCursor(textarea, '∑'); break;
            case 'integral': insertAtCursor(textarea, '∫'); break;
            case 'leq': insertAtCursor(textarea, '≤'); break;
            case 'geq': insertAtCursor(textarea, '≥'); break;
            case 'neq': insertAtCursor(textarea, '≠'); break;
            case 'infty': insertAtCursor(textarea, '∞'); break;
            case 'plusminus': insertAtCursor(textarea, '±'); break;
            case 'times': insertAtCursor(textarea, '×'); break;
            case 'divide': insertAtCursor(textarea, '÷'); break;
        }
    }

    // ===== DOM Ready =====
    document.addEventListener('DOMContentLoaded', function () {
        // math buttons
        document.querySelectorAll('.math-btn').forEach(btn => {
            btn.addEventListener('click', function (e) {
                const action = this.dataset.action;
                const targetId = this.dataset.target;
                const ta = document.getElementById(targetId);
                if (!ta) return;
                handleAction(action, ta);
            });
        });

        // symbol dropdowns
        document.querySelectorAll('.math-symbols').forEach(sel => {
            sel.addEventListener('change', function () {
                const action = this.value;
                const targetId = this.dataset.target;
                if (!action) return;
                const ta = document.getElementById(targetId);
                if (!ta) {
                    this.value = '';
                    return;
                }
                handleAction(action, ta);
                this.value = '';
            });
        });

        // initial charcounts and listeners for all textareas having data-charcount
        document.querySelectorAll('textarea[data-charcount]').forEach(ta => {
            // initialize
            updateCharCountFor(ta);
            // input listener
            ta.addEventListener('input', () => updateCharCountFor(ta));
        });
    });
})();
