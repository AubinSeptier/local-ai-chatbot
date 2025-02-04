import { useState, useEffect } from 'react';
import LoginForm from './components/auth/LoginForm';
import ChatContainer from './components/Chat/ChatContainer';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [darkMode, setDarkMode] = useState(false);

  const toggleDarkMode = () => setDarkMode(!darkMode);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch('http://localhost:7860/api/check-auth', {
        credentials: 'include'
      });
      setIsAuthenticated(response.ok);
    } catch (error) {
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('http://localhost:7860/api/logout', {
        method: 'POST',
        credentials: 'include'
      });
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-gray-900 dark:border-gray-100"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginForm onLogin={() => setIsAuthenticated(true)} />;
  }

  return (
    <div className={`h-screen ${darkMode ? 'dark' : ''}`}>
      <div className="h-full flex flex-col bg-white dark:bg-gray-800"> {/* Modification ici */}
        <ChatContainer onLogout={handleLogout} darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
      </div>
    </div>
  );
}