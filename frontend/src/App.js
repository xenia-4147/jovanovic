import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from './components/ui/toaster';
import { AuthProvider } from './contexts/AuthContext';
import HomePage from './pages/HomePage';
import CreateCardPage from './pages/CreateCardPage';
import ViewCardPage from './pages/ViewCardPage';
import EditCardPage from './pages/EditCardPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import AddressBookPage from './pages/AddressBookPage';
import ProtectedRoute from './components/ProtectedRoute';
import "./App.css";

function App() {
  return (
    <div className="App min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/card/:id" element={<ViewCardPage />} />
            <Route path="/create-test" element={<CreateCardPage />} />
            <Route path="/" element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            } />
            <Route path="/create" element={
              <ProtectedRoute>
                <CreateCardPage />
              </ProtectedRoute>
            } />
            <Route path="/edit/:id" element={
              <ProtectedRoute>
                <EditCardPage />
              </ProtectedRoute>
            } />
          </Routes>
        </Router>
        <Toaster />
      </AuthProvider>
    </div>
  );
}

export default App;