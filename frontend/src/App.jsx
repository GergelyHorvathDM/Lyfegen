import { useState } from 'react'
import Chat from './components/Chat'
import Auth from './components/Auth'

function App() {
  const [apiKey, setApiKey] = useState(() => {
    return localStorage.getItem('apiKey') || null;
  });

  const handleLogin = (key) => {
    localStorage.setItem('apiKey', key)
    setApiKey(key)
  }

  const handleLogout = () => {
    localStorage.removeItem('apiKey')
    setApiKey(null)
  }

  return (
    <div className="h-screen">
      {apiKey ? <Chat apiKey={apiKey} onLogout={handleLogout} /> : <Auth onLogin={handleLogin} />}
    </div>
  )
}

export default App
