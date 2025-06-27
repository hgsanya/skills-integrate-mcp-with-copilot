document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  
  // Authentication elements
  const loginBtn = document.getElementById("login-btn");
  const loginModal = document.getElementById("login-modal");
  const loginForm = document.getElementById("login-form");
  const loginMessage = document.getElementById("login-message");
  const authStatus = document.getElementById("auth-status");
  const teacherName = document.getElementById("teacher-name");
  const logoutBtn = document.getElementById("logout-btn");
  const closeModal = document.querySelector(".close");

  let authToken = localStorage.getItem("teacher_token");

  // Check authentication status on load
  checkAuthStatus();

  // Authentication event listeners
  loginBtn.addEventListener("click", () => {
    loginModal.classList.remove("hidden");
  });

  closeModal.addEventListener("click", () => {
    loginModal.classList.add("hidden");
    clearLoginForm();
  });

  loginModal.addEventListener("click", (e) => {
    if (e.target === loginModal) {
      loginModal.classList.add("hidden");
      clearLoginForm();
    }
  });

  logoutBtn.addEventListener("click", logout);

  loginForm.addEventListener("submit", handleLogin);

  function clearLoginForm() {
    loginForm.reset();
    loginMessage.classList.add("hidden");
  }

  async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const result = await response.json();

      if (response.ok) {
        authToken = result.access_token;
        localStorage.setItem("teacher_token", authToken);
        loginModal.classList.add("hidden");
        clearLoginForm();
        updateAuthUI(true, result.teacher_name);
        showMessage("Login successful!", "success");
      } else {
        loginMessage.textContent = result.detail || "Login failed";
        loginMessage.className = "error";
        loginMessage.classList.remove("hidden");
      }
    } catch (error) {
      loginMessage.textContent = "Login failed. Please try again.";
      loginMessage.className = "error";
      loginMessage.classList.remove("hidden");
      console.error("Login error:", error);
    }
  }

  async function checkAuthStatus() {
    if (!authToken) {
      updateAuthUI(false);
      return;
    }

    try {
      const response = await fetch("/auth/verify", {
        headers: {
          "Authorization": `Bearer ${authToken}`,
        },
      });

      const result = await response.json();

      if (result.authenticated) {
        updateAuthUI(true, result.teacher_name);
      } else {
        logout();
      }
    } catch (error) {
      console.error("Auth check failed:", error);
      logout();
    }
  }

  function logout() {
    authToken = null;
    localStorage.removeItem("teacher_token");
    updateAuthUI(false);
    showMessage("Logged out successfully", "success");
  }

  function updateAuthUI(isAuthenticated, name = "") {
    if (isAuthenticated) {
      loginBtn.classList.add("hidden");
      authStatus.classList.remove("hidden");
      teacherName.textContent = `Welcome, ${name}`;
      
      // Enable form controls
      signupForm.classList.remove("disabled");
      document.getElementById("email").disabled = false;
      document.getElementById("activity").disabled = false;
      document.querySelector('#signup-form button[type="submit"]').disabled = false;
    } else {
      loginBtn.classList.remove("hidden");
      authStatus.classList.add("hidden");
      teacherName.textContent = "";
      
      // Disable form controls
      signupForm.classList.add("disabled");
      document.getElementById("email").disabled = true;
      document.getElementById("activity").disabled = true;
      document.querySelector('#signup-form button[type="submit"]').disabled = true;
    }
  }

  function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.classList.remove("hidden");
    
    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons (only for authenticated teachers)
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li>
                        <span class="participant-email">${email}</span>
                        ${authToken ? `<button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button>` : ''}
                      </li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    if (!authToken) {
      showMessage("Teacher login required to unregister students", "error");
      return;
    }

    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
          headers: {
            "Authorization": `Bearer ${authToken}`,
          },
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        fetchActivities();
      } else if (response.status === 401) {
        showMessage("Authentication expired. Please login again.", "error");
        logout();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!authToken) {
      showMessage("Teacher login required to register students", "error");
      return;
    }

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${authToken}`,
          },
          body: JSON.stringify({ email }),
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        signupForm.reset();
        fetchActivities();
      } else if (response.status === 401) {
        showMessage("Authentication expired. Please login again.", "error");
        logout();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
