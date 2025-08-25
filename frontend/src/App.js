import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from './components/ui/toaster';
import HomePage from './pages/HomePage';
import CreateCardPage from './pages/CreateCardPage';
import ViewCardPage from './pages/ViewCardPage';
import EditCardPage from './pages/EditCardPage';
import "./App.css";

function App() {
  return (
    <div className="App min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/create" element={<CreateCardPage />} />
          <Route path="/card/:id" element={<ViewCardPage />} />
          <Route path="/edit/:id" element={<EditCardPage />} />
        </Routes>
      </Router>
      <Toaster />
    </div>
  );
}

export default App;