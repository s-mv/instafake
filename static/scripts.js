document.addEventListener("DOMContentLoaded", () => {
    const loginModal = document.getElementById("login-modal");
    const loginBtn = document.getElementById("login-btn");
    const logoutBtn = document.getElementById("logout-btn");
    const closeModal = document.querySelector(".close");
    const uploadSection = document.getElementById("upload-section");

    // Show login modal
    loginBtn.addEventListener("click", () => {
        loginModal.style.display = "flex";
    });

    // Close login modal
    closeModal.addEventListener("click", () => {
        loginModal.style.display = "none";
    });

    // Handle login
    document.getElementById("login-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const response = await fetch("/login", {
            method: "POST",
            body: formData,
        });
        const data = await response.json();
        if (response.ok) {
            localStorage.setItem("username", formData.get("username")); // Store username instead of user_id
            loginModal.style.display = "none";
            loginBtn.style.display = "none";
            logoutBtn.style.display = "block";
            uploadSection.style.display = "block";
            loadFeed();
        } else {
            alert(data.detail);
        }
    });

    // Handle register
    document.getElementById("register-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const response = await fetch("/register", {
            method: "POST",
            body: formData,
        });
        const data = await response.json();
        if (response.ok) {
            alert("Registration successful! Please log in.");
        } else {
            alert(data.detail);
        }
    });

    // Handle logout
    logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("username");
        loginBtn.style.display = "block";
        logoutBtn.style.display = "none";
        uploadSection.style.display = "none";
        document.getElementById("feed").innerHTML = "";
    });

    // Handle upload
    document.getElementById("upload-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = localStorage.getItem("username"); // Use username instead of user_id
        if (!username) {
            alert("You must be logged in to upload a post.");
            return;
        }
        const formData = new FormData(e.target);
        formData.append("user_id", username); // Send username as user_id
        const response = await fetch("/upload", {
            method: "POST",
            body: formData,
        });
        const data = await response.json();
        if (response.ok) {
            alert("Post uploaded successfully!");
            loadFeed();
        } else {
            alert(data.detail || "Failed to upload post.");
        }
    });

    // Load feed
    async function loadFeed() {
        const username = localStorage.getItem("username");
        if (!username) return;
        const response = await fetch(`/feed?user_id=${username}`);
        const posts = await response.json();

        // Ensure posts is an array
        if (!Array.isArray(posts)) {
            console.error("Unexpected response format:", posts);
            alert("Failed to load feed. Please try again.");
            return;
        }

        const feed = document.getElementById("feed");
        feed.innerHTML = posts
            .map(
                (post) =>
                    `<div>
                        <p>From <strong>${post.username}</strong></p>
                        <img src="${post.image_url}" alt="${post.caption}">
                        <p>${post.caption}</p>
                    </div>`
            )
            .join("");
    }

    // Check login state on page load
    if (localStorage.getItem("username")) {
        loginBtn.style.display = "none";
        logoutBtn.style.display = "block";
        uploadSection.style.display = "block";
        loadFeed();
    }

    // Clear cache
    document.getElementById("clear-cache-btn").addEventListener("click", () => {
        localStorage.clear();
        alert("Cache cleared!");
        location.reload();
    });
});
