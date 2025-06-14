import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Stand App Up</h1>
        <p>React frontend connected to Django backend with PostgreSQL</p>
        <div className="app-info">
          <div className="tech-stack">
            <h3>Technology Stack:</h3>
            <ul>
              <li>Frontend: React with TypeScript</li>
              <li>Backend: Django with Django REST Framework</li>
              <li>Database: PostgreSQL</li>
              <li>Package Management: pipenv (Django), npm (React)</li>
            </ul>
          </div>
        </div>
      </header>
    </div>
  );
}

export default App;