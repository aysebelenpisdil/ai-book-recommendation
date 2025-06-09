
// App.js or your main component
import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Home from "./components/Home";
import Login from "./components/Login";
import Search from "./components/Search";
// Import other components as needed

export default function App() {
    const [user, setUser] = useState(null);

    // Check for existing user in localStorage on app load
    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            setUser(JSON.parse(storedUser));
        }
    }, []);

    // Function to handle logout
    const handleLogout = () => {
        localStorage.removeItem('user');
        setUser(null);
    };

    return (
        <Router>
            <div className="app-container">
                {/* Navigation bar or header with logout if user is logged in */}
                {user && (
                    <header>
                        <nav>
                            {/* Your navigation items */}
                            <button onClick={handleLogout}>Çıkış Yap</button>
                        </nav>
                    </header>
                )}

                <Routes>
                    {/* Protected routes - redirect to login if not authenticated */}
                    <Route 
                        path="/" 
                        element={user ? <Home user={user} /> : <Navigate to="/login" />} 
                    />
                    <Route 
                        path="/search" 
                        element={user ? <Search user={user} /> : <Navigate to="/login" />} 
                    />

                    {/* Public routes */}
                    <Route path="/login" element={<Login />} />

                    {/* Add more routes as needed */}
                </Routes>
            </div>
        </Router>
    );
}
