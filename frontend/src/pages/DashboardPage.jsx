import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { ShieldCheck, Clock, FileText, ArrowRight, Loader2, Plus } from 'lucide-react';

const DashboardPage = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await api.get('/analytics/dashboard');
        setStats(response.data);
      } catch (error) {
        console.error("Failed to load dashboard stats", error);
        // Fallback for UI if backend isn't ready
        setStats({ matched_schemes: 0, pending_tasks: 0, uploaded_documents: 0 });
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  const StatCard = ({ title, value, icon: Icon, color, linkTo }) => (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500 mb-1">{title}</p>
          <h3 className="text-3xl font-bold text-slate-900">{value}</h3>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
      <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
        <span className="text-xs text-slate-500">Updated just now</span>
        {linkTo && (
          <Link to={linkTo} className="text-sm font-medium text-primary flex items-center hover:underline">
            View Details <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Welcome, {user?.user_metadata?.full_name?.split(' ')[0] || 'Citizen'}
          </h1>
          <p className="text-slate-600 mt-1">Here's your government scheme application overview.</p>
        </div>
        
        <Link 
          to="/eligibility" 
          className="inline-flex items-center gap-2 bg-primary text-white font-medium px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" />
          New Eligibility Check
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          title="Matched Schemes" 
          value={stats?.matched_schemes || 0} 
          icon={ShieldCheck} 
          color="bg-green-100 text-green-600"
          linkTo="/schemes"
        />
        <StatCard 
          title="Pending Checklist Tasks" 
          value={stats?.pending_tasks || 0} 
          icon={Clock} 
          color="bg-orange-100 text-orange-600"
          linkTo="/checklists"
        />
        <StatCard 
          title="Uploaded Documents" 
          value={stats?.uploaded_documents || 0} 
          icon={FileText} 
          color="bg-blue-100 text-blue-600"
          linkTo="/documents"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        {/* Quick Actions Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <Link to="/documents" className="flex items-center justify-between p-4 rounded-lg border border-slate-100 hover:bg-slate-50 hover:border-slate-300 transition-all group">
              <div className="flex items-center gap-4">
                <div className="bg-blue-50 p-2 rounded-md text-blue-600 group-hover:bg-blue-100">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-medium text-slate-900 text-sm">Upload Aadhaar</h4>
                  <p className="text-xs text-slate-500 mt-0.5">We'll automatically extract your details</p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-primary transition-colors" />
            </Link>
            
            <Link to="/eligibility" className="flex items-center justify-between p-4 rounded-lg border border-slate-100 hover:bg-slate-50 hover:border-slate-300 transition-all group">
              <div className="flex items-center gap-4">
                <div className="bg-indigo-50 p-2 rounded-md text-indigo-600 group-hover:bg-indigo-100">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-medium text-slate-900 text-sm">Update Profile</h4>
                  <p className="text-xs text-slate-500 mt-0.5">Recalculate your scheme eligibility</p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-primary transition-colors" />
            </Link>
          </div>
        </div>

        {/* Empty State for Recent Activity */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col items-center justify-center text-center min-h-[300px]">
          <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4 border border-slate-100">
            <Clock className="w-8 h-8 text-slate-300" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-1">No Recent Activity</h3>
          <p className="text-slate-500 text-sm max-w-sm mb-6">
            Run your first eligibility check to discover government schemes you qualify for.
          </p>
          <Link to="/eligibility" className="bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 font-medium px-4 py-2 rounded-lg text-sm transition-colors shadow-sm">
            Check Eligibility
          </Link>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
