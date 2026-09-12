import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Shield,
  AlertTriangle,
  Users,
  FileText,
  ChevronRight,
  Activity
} from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();

  const menuItems = [
    { path: '/', label: 'Dashboard', icon: Shield },
    { path: '/alerts', label: 'Alerts', icon: AlertTriangle },
    { path: '/user-activity', label: 'User Activity', icon: Users },
    { path: '/reports', label: 'Reports', icon: FileText },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="w-64 bg-gradient-to-b from-slate-800 to-slate-900 text-white h-screen shadow-xl overflow-y-auto">
      {/* Header */}
      <div className="px-6 py-8 border-b border-slate-700">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-blue-600 rounded-lg flex items-center justify-center">
            <Shield size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold">DataShield</h1>
            <p className="text-xs text-slate-400">DLP & Threat Detection</p>
          </div>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="px-4 py-6">
        <div className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group ${
                  active
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                }`}
              >
                <Icon size={20} />
                <span className="flex-1 font-medium">{item.label}</span>
                {active && <ChevronRight size={18} className="opacity-0 group-hover:opacity-100" />}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Status Section */}
      <div className="px-6 py-6 mt-auto border-t border-slate-700">
        <div className="bg-slate-700 bg-opacity-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity size={16} className="text-green-400" />
            <span className="text-sm font-semibold">System Status</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-xs text-slate-300">Monitoring Active</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-slate-700 text-center">
        <p className="text-xs text-slate-400">v1.0.0</p>
      </div>
    </div>
  );
};

export default Sidebar;
