import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Alerts from './pages/Alerts';
import Investigation from './pages/Investigation';
import UserActivity from './pages/UserActivity';
import Reports from './pages/Reports';
import './styles/index.css';

function App() {
  const [, setActiveAlert] = React.useState(null);

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <div className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/alerts" element={<Alerts onAlertSelect={setActiveAlert} />} />
            <Route path="/investigation/:alertId" element={<Investigation />} />
            <Route path="/user-activity" element={<UserActivity />} />
            <Route path="/reports" element={<Reports />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
