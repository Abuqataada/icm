document.querySelectorAll('.tab-button').forEach(button => {
	button.addEventListener('click', () => {
		const tabId = button.getAttribute('data-tab');

		document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
		document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

		button.classList.add('active');
		document.getElementById(tabId).classList.add('active');
	});
});

document.querySelector('.login-link').addEventListener('click', () => {
	document.querySelector('.tab-button[data-tab="login"]').click();
});


document.addEventListener('DOMContentLoaded', function() {
    fetch('/get-schools')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const select = document.getElementById('school-dropdown');
            const selectlogin = document.getElementById('school');
            
            if (data.schools && data.schools.length > 0) {
                data.schools.forEach(school => {
                    const option = document.createElement('option');
                    option.value = school.id;
                    option.textContent = school.name;
                    select.appendChild(option);
                    selectlogin.appendChild(option);
                });
            } else {
                console.error("No schools found in the response.");
            }
        })
        .catch(error => {
            console.error("Failed to fetch schools:", error);
        });
});

window.onload = function() {
    setTimeout(function() {
        var flashes = document.getElementsByClassName('flash');
        for (var i = 0; i < flashes.length; i++) {
            flashes[i].style.opacity = '0';
            setTimeout(function(flash) {
                flash.style.display = 'none';
            }, 500, flashes[i]); // Adjust the time to match the transition duration
        }
    }, 3000); // Adjust the duration the flash message should be visible (in milliseconds)
    };





// SPINNER FUNCTION
document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault(); // Prevent immediate form submission
    
    const container = document.querySelector('.container');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const backgroundOverlay = document.getElementById('backgroundOverlay');
    
    // Add hide class to animate opacity and height
    container.classList.add('hide');
    
    // Once the transition ends, set display to none and show the spinner
    container.addEventListener('transitionend', () => {
        container.style.display = 'none';
        backgroundOverlay.style.opacity = '0.3'; // Set desired opacity for the overlay
        //body.style.opacity = '0.5';
        loadingSpinner.style.display = 'block';
    }, { once: true });
    
    // Wait for 3 seconds before submitting the form
    setTimeout(() => {
        document.getElementById('loginForm').submit(); // Submit form programmatically
    }, 3000); // 3000ms = 3 seconds delay
});