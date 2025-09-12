function openNav() {
    document.getElementById("mySidebar").style.width = "250px";
    document.getElementById("main").style.marginLeft = "250px";
    document.querySelector(".openbtn").style.display = "none"; // Hide the button
  }
  
function closeNav() {
    document.getElementById("mySidebar").style.width = "0";
    document.getElementById("main").style.marginLeft= "0";
    document.querySelector(".openbtn").style.display = "inline-block"; // Show the button
  }






    // ===== Utility Functions for Math Symbols =====
    function toSuperscript(num) {
        const map = {"0":"⁰","1":"¹","2":"²","3":"³","4":"⁴","5":"⁵","6":"⁶","7":"⁷","8":"⁸","9":"⁹"};
        return num.toString().split('').map(d => map[d] || d).join('');
    }

    function toSubscript(num) {
        const map = {"0":"₀","1":"₁","2":"₂","3":"₃","4":"₄","5":"₅","6":"₆","7":"₇","8":"₈","9":"₉"};
        return num.toString().split('').map(d => map[d] || d).join('');
    }

    // ===== Main insertion function =====
    function insertAtCursor(type) {
        const textarea = document.getElementById('question_text');
        const startPos = textarea.selectionStart;
        const endPos = textarea.selectionEnd;
        const currentValue = textarea.value;
        
        let insertText = '';
        let promptText = '';
        let userInput = '';
        
        switch(type) {
            case 'power':
                promptText = "Enter the exponent (e.g., 2 for x²):";
                userInput = prompt(promptText);
                if (userInput !== null) insertText = toSuperscript(userInput);
                break;
                
            case 'subscript':
                promptText = "Enter the subscript (e.g., 2 for x₂):";
                userInput = prompt(promptText);
                if (userInput !== null) insertText = toSubscript(userInput);
                break;
                
            case 'root':
                promptText = "Enter the root index (e.g., 3 for cube root):";
                userInput = prompt(promptText);
                if (userInput !== null) {
                    if (isNaN(userInput) || userInput < 2) {
                        alert("Please enter a valid number ≥ 2");
                        return;
                    }
                    insertText = userInput == 2 ? '√' : `${toSuperscript(userInput)}√`;
                }
                break;
                
            case 'fraction':
                promptText = "Enter fraction (e.g., '1/2' for ½):";
                userInput = prompt(promptText);
                if (userInput !== null) {
                    const parts = userInput.split('/');
                    if (parts.length === 2) {
                        insertText = `${toSuperscript(parts[0])}⁄${toSubscript(parts[1])}`;
                    } else {
                        alert("Please enter fraction in format 'numerator/denominator'");
                    }
                }
                break;
                
            // === Greek and math symbols ===
            case 'pi': insertText = 'π'; break;
            case 'theta': insertText = 'θ'; break;
            case 'sigma': insertText = '∑'; break;
            case 'integral': insertText = '∫'; break;
            case 'leq': insertText = '≤'; break;
            case 'geq': insertText = '≥'; break;
            case 'neq': insertText = '≠'; break;
            case 'infty': insertText = '∞'; break;
            case 'plusminus': insertText = '±'; break;
            case 'times': insertText = '×'; break;
            case 'divide': insertText = '÷'; break;
        }
        
        if (insertText) {
            textarea.value = currentValue.substring(0, startPos) + insertText + currentValue.substring(endPos);
            
            // Move cursor after inserted text
            const newPos = startPos + insertText.length;
            textarea.setSelectionRange(newPos, newPos);
            textarea.focus();
            
            // Update character count
            document.getElementById('charCount').textContent = `${textarea.value.length}/1000 characters`;
        }
    }

    // ===== Clear form function =====
    function clearForm() {
        if (confirm('Are you sure you want to clear the form? All entered data will be lost.')) {
            document.getElementById('questionForm').reset();
            document.getElementById('charCount').textContent = '0/1000 characters';
            document.getElementById('imagePreview').style.display = 'none';
            document.getElementById('validationErrors').classList.add('d-none');
        }
    }

    // ===== DOM Ready Setup =====
    document.addEventListener('DOMContentLoaded', function() {
        const questionText = document.getElementById('question_text');
        const charCount = document.getElementById('charCount');
        const imageInput = document.getElementById('image');
        const imagePreview = document.getElementById('imagePreview');
        const previewImg = document.getElementById('previewImg');
        const removeImageBtn = document.getElementById('removeImageBtn');

        // --- Character counter ---
        questionText.addEventListener('input', function() {
            const length = this.value.length;
            charCount.textContent = `${length}/1000 characters`;
            if (length > 900) {
                charCount.classList.add('text-danger');
            } else {
                charCount.classList.remove('text-danger');
            }
        });

        // --- Image preview ---
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                if (file.size > 4 * 1024 * 1024) {
                    alert('File size must be less than 4MB');
                    this.value = '';
                    return;
                }
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    imagePreview.style.display = 'block';
                }
                reader.readAsDataURL(file);
            }
        });

        if (removeImageBtn) {
            removeImageBtn.addEventListener('click', function() {
                imageInput.value = '';
                imagePreview.style.display = 'none';
            });
        }

        // --- Toolbar buttons ---
        document.querySelectorAll('#toolbar button').forEach(button => {
            button.addEventListener('click', function() {
                const action = this.getAttribute('data-action');
                insertAtCursor(action);
            });
        });

        // --- Clear form ---
        document.getElementById('clearFormButton').addEventListener('click', clearForm);

        // --- Form validation ---
        document.getElementById('questionForm').addEventListener('submit', function(e) {
            const errors = [];
            const optionA = document.getElementById('option_a').value.trim();
            const optionB = document.getElementById('option_b').value.trim();
            const optionC = document.getElementById('option_c').value.trim();
            const optionD = document.getElementById('option_d').value.trim();
            const correctAnswer = document.getElementById('correct_answer').value;

            if (!questionText.value.trim()) errors.push('Question text is required');
            if (questionText.value.length > 1000) errors.push('Question text cannot exceed 1000 characters');
            if (!optionA) errors.push('Option A is required');
            if (!optionB) errors.push('Option B is required');
            if (!optionC) errors.push('Option C is required');
            if (!optionD) errors.push('Option D is required');
            if (!correctAnswer) errors.push('Please select the correct answer');

            if (errors.length > 0) {
                e.preventDefault();
                const errorList = document.getElementById('errorList');
                const validationErrors = document.getElementById('validationErrors');
                
                errorList.innerHTML = '';
                errors.forEach(error => {
                    const li = document.createElement('li');
                    li.textContent = error;
                    errorList.appendChild(li);
                });
                
                validationErrors.classList.remove('d-none');
                validationErrors.scrollIntoView({ behavior: 'smooth' });
            }
        });

        // --- Math symbols dropdown ---
        document.getElementById('mathSymbols').addEventListener('change', function() {
            const action = this.value;
            if (action) {
                insertAtCursor(action);
                this.value = ""; // reset dropdown after inserting
            }
        });

        // --- Auto-hide flash messages ---
        setTimeout(function() {
            const flashes = document.querySelectorAll('.alert:not(.alert-danger)');
            flashes.forEach(flash => {
                flash.style.opacity = '0';
                setTimeout(() => flash.remove(), 500);
            });
        }, 5000);
    });
