document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();
    
    // Mock login validation (This will be connected to Python later)
    let username = document.getElementById('username').value;
    let password = document.getElementById('password').value;

    if(username === 'admin' && password === 'admin123') {
        window.location.href = "dashboard.html";
    } else {
        alert('Invalid username or password');
    }
});
