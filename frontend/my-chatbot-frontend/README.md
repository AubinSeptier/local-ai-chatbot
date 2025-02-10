# Frontend

This folder contains the frontend of the project.
This project used React.js with Vite and Tailwind CSS for the frontend. 

## Architecture and code structure 

The frontend is composed of the main following components in the `src` folder :

* `App.jsx` : Main component of the application.
* `api/chatApi.js` : Manage the communication with the backend.
* `components/auth/LoginForm.jsx` : Register and login form.
* `components/Chat/ChatBubble.jsx` : Display the chat messages with Markdown support.
* `components/Chat/ChatContainer.jsx` : Orchestrates all elements of the chat interface (conversation list, message display, user input, etc).
* `components/Chat/ConversationList.jsx` : Display the list of conversations.
* `components/Chat/DarkModeToggle.jsx` : Switches from light to dark mode and vice versa
* `components/hooks/useChat.js` : Centralizes and manages chat communication logic, conversation and message management in the frontend.