import { useState } from 'react';

const Auth = ({ onLogin }) => {
  const [key, setKey] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    // The parent component will handle the logic of setting the key
    onLogin(key);
    // We don't need to check for success here, as the parent will re-render
    // If the key were incorrect, the parent would not switch to the Chat component
  };

  return (
    <div className="flex items-center justify-center h-screen bg-gray-900 font-sans">
      <div className="w-full max-w-md p-8 space-y-8 bg-gray-800 rounded-2xl shadow-2xl">
        <div className="text-center">
            <img src="/lyfegenhealth_logo.jpeg" alt="Lyfegen Logo" className="w-20 h-20 mx-auto rounded-full border-4 border-indigo-500/50 mb-4"/>
            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
                Document Intelligence
            </h1>
            <p className="mt-2 text-gray-400">Please enter your access key to continue.</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="relative">
            <input
              type="password"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="Your API Key"
              className="w-full px-5 py-3 text-lg text-white bg-gray-700 border border-gray-600 rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-shadow"
            />
          </div>
          {error && <p className="text-sm text-center text-red-400">{error}</p>}
          <div>
            <button
              type="submit"
              className="w-full px-6 py-3 font-semibold text-white bg-indigo-600 rounded-full hover:bg-indigo-700 disabled:bg-indigo-500/50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-indigo-500 transition-transform transform hover:scale-105"
            >
              Unlock
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Auth; 