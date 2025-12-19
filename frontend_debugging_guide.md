**Debugging "User Not Authenticated" on the Frontend**

The backend seems to have a solid authentication implementation, supporting both Firebase ID tokens and internal JWTs, and correctly interacting with Firebase Authentication and Firestore. This strongly suggests the issue lies within the frontend application.

To effectively debug this, please investigate the following on your frontend:

1.  **Browser Developer Tools (Network Tab):**
    *   Open your browser's developer tools (usually F12 or right-click -> Inspect -> Network tab).
    *   Perform a login action on your frontend.
    *   Observe the network requests made.
    *   **Look for:**
        *   **Login Request:** Identify the request sent to your backend's `/api/v1/auth/login` (or `/register`, `/google`).
        *   **Response:** Check the response for this request. Does it contain `access_token` and `refresh_token`? Is the `status` code 200 OK?
        *   **Subsequent Protected Requests:** After a successful login, navigate to a page that requires authentication (e.g., a profile page that calls `/api/v1/auth/me`).
        *   **Authorization Header:** For these protected requests, examine the request headers. Do you see an `Authorization: Bearer <your_access_token>` header? Is the token present and correctly formatted?
        *   **Status Codes:** If a protected request fails, what HTTP status code is returned (e.g., 401 Unauthorized, 403 Forbidden)?

2.  **Frontend Storage (Application Tab):**
    *   After a successful login, check your browser's "Application" tab (Developer Tools).
    *   **Local Storage/Session Storage/Cookies:** Where is your frontend storing the `access_token` and `refresh_token`? Verify that the tokens are indeed being stored after login.

3.  **Frontend Code Review:**
    *   **Token Handling:** Review the frontend code responsible for:
        *   **Storing Tokens:** How are the `access_token` and `refresh_token` saved after a successful login response? (e.g., `localStorage.setItem`, Redux store, Context API).
        *   **Attaching Tokens to Requests:** How are these stored tokens retrieved and attached to outgoing requests to the backend? (e.g., using Axios interceptors, Fetch API headers). Ensure the `Authorization` header is correctly set as `Bearer <token>`.
        *   **Authentication State:** How does your frontend determine if a user is authenticated? Is it checking for the presence and validity of the stored token, or is it relying on a backend call that might be failing?
    *   **Firebase SDK Usage (if applicable):** If your frontend is using the Firebase Client SDK for authentication (e.g., `signInWithEmailAndPassword`, `signInWithPopup`), ensure:
        *   The Firebase SDK is correctly initialized.
        *   You are listening to `onAuthStateChanged` to get the current Firebase user.
        *   You are correctly obtaining the Firebase ID Token (`firebase.auth().currentUser.getIdToken()`) and passing it to the backend's `/login` or `/google` endpoints if that's the intended flow.

4.  **CORS Issues:**
    *   While less likely if some requests are working, if you see any `CORS` related errors in the browser console, this could indicate a configuration issue preventing the `Authorization` header from being correctly sent or received.

Please provide specific details from these investigations (e.g., exact network tab output for a failed protected request, relevant frontend code snippets) for further assistance.